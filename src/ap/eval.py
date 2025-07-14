"""Evaluation module for running agent tests against datasets."""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any

from anyio import run
from dotenv import load_dotenv
from langfuse import get_client
from openai import AsyncOpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
import yaml

from src.ap.actions import Done
from src.ap.agent import go
from src.ap.config import Config
from src.ap.context import Context
from src.ap.either import Left, Right
from src.ap.inmemory import ThreadInMemoryStore
from src.ap.thread import Thread


@dataclass
class TestCase:
    """Represents a single test case from the evaluation dataset."""
    id: str
    prompt: str
    expected_answer: Any
    expected_steps: list[str]
    user_input: str | list[str] | None = None


@dataclass
class EvaluationResult:
    """Results of evaluating a single test case."""
    test_id: str
    thread_id: str
    task_completed: bool
    result_valid: bool
    step_count_match: bool
    expected_actions_found: bool
    actual_result: Any
    actual_steps: list[str]
    error_message: str | None = None


class MockTyper:
    """Mock typer object that returns predefined user input."""
    
    def __init__(self, user_input: str | list[str] | None = None):
        if isinstance(user_input, list):
            self.user_inputs = user_input
            self.current_index = 0
        elif user_input is not None:
            self.user_inputs = [user_input]
            self.current_index = 0
        else:
            self.user_inputs = []
            self.current_index = 0
    
    def prompt(self, message: str) -> str:
        """Return the next predefined user input."""
        if self.current_index < len(self.user_inputs):
            response = self.user_inputs[self.current_index]
            self.current_index += 1
            return response
        return ""
    
    def echo(self, message: str) -> None:
        """Mock echo that does nothing."""
        pass


def load_dataset(dataset_path: str) -> list[TestCase]:
    """Load test cases from a YAML dataset file."""
    with open(dataset_path) as f:
        data = yaml.safe_load(f)
    
    test_cases = []
    for item in data:
        test_cases.append(TestCase(
            id=item['id'],
            prompt=item['prompt'],
            expected_answer=item['expected_answer'],
            expected_steps=item['expected_steps'],
            user_input=item.get('user_input')
        ))
    
    return test_cases


def extract_action_types(steps: list[str]) -> list[str]:
    """Extract action types from step strings."""
    action_types = []
    for step in steps:
        # Extract action name from strings like "Add(a=1, b=2)"
        if '(' in step:
            action_name = step.split('(')[0]
            action_types.append(action_name)
    return action_types


def _normalize_action_name(action_name: str) -> str:
    """Normalize action names for comparison."""
    # Map variations to standard names
    name_map = {
        "RequestUserInput": "AskUser",
        "AskUser": "AskUser",
    }
    return name_map.get(action_name, action_name)


def _compare_results(actual: Any, expected: Any) -> bool:
    """Compare actual and expected results with flexible formatting."""
    if actual is None and expected is None:
        return True
    
    if actual is None or expected is None:
        return False
    
    # Handle special cases
    if expected == "refusal":
        # For refusal cases, check if the actual result is not a number
        try:
            float(str(actual))
            return False  # If it's a number, it's not a refusal
        except (ValueError, TypeError):
            return True  # If it's not a number, it's a refusal
    
    # Try to convert both to float for numeric comparison
    try:
        actual_float = float(str(actual).replace(',', '.'))
        expected_float = float(str(expected).replace(',', '.'))
        # Allow for small floating point errors
        return abs(actual_float - expected_float) < 1e-3
    except (ValueError, TypeError):
        pass
    
    # Fallback to string comparison
    return str(actual).strip() == str(expected).strip()


def evaluate_test_case(
    test_case: TestCase, driver: str
) -> tuple[EvaluationResult, ThreadInMemoryStore]:
    """Evaluate a single test case."""
    # Set up context with mock typer for user input
    mock_typer = MockTyper(test_case.user_input)
    
    # Initialize state store
    thread_store = ThreadInMemoryStore()
    
    # Initialize context
    context = Context(
        client=AsyncOpenAI(),
        logger=logging.getLogger(__name__),
        langfuse=get_client(),
        cli=mock_typer, # type: ignore
        state=thread_store,
        driver=driver,
    )
    
    # Create and store thread
    thread = Thread(query=test_case.prompt)
    thread_store.add(thread)
    
    # Run the agent
    try:
        result = run(go, context, thread.id, backend="asyncio")
        
        # Get the updated thread to extract steps
        updated_thread_result = thread_store.get(thread.id)
        if isinstance(updated_thread_result, Left):
            raise Exception(f"Failed to get thread: {updated_thread_result.error}")
        
        assert isinstance(updated_thread_result, Right)
        updated_thread = updated_thread_result.value
        
        # Extract actual steps and result
        actual_steps = list({str(action) for action in updated_thread.actions})
        actual_result = None
        task_completed = False
        error_message = None
        
        if isinstance(result, Right):
            action = result.value
            if isinstance(action, Done):
                actual_result = action.output
                task_completed = True
        elif isinstance(result, Left):
            error_message = result.error
            task_completed = False
        
        # Calculate subscores
        result_valid = _compare_results(actual_result, test_case.expected_answer)
        step_count_match = len(actual_steps) == len(test_case.expected_steps)
        
        # Check if expected actions are found
        expected_action_types = extract_action_types(test_case.expected_steps)
        actual_action_types = extract_action_types(actual_steps)
        normalized_actual_actions = [
            _normalize_action_name(a) for a in actual_action_types
        ]
        expected_actions_found = all(
            _normalize_action_name(action_type) in normalized_actual_actions
            for action_type in expected_action_types
        )
        
        return EvaluationResult(
            test_id=test_case.id,
            thread_id=thread.id,
            task_completed=task_completed,
            result_valid=result_valid,
            step_count_match=step_count_match,
            expected_actions_found=expected_actions_found,
            actual_result=actual_result,
            actual_steps=actual_steps,
            error_message=error_message
        ), thread_store
        
    except Exception as e:
        return EvaluationResult(
            test_id=test_case.id,
            thread_id=thread.id,
            task_completed=False,
            result_valid=False,
            step_count_match=False,
            expected_actions_found=False,
            actual_result=None,
            actual_steps=[],
            error_message=str(e)
        ), thread_store


def save_thread_details(
    thread_id: str, thread_store: ThreadInMemoryStore, thread_dir: str
) -> None:
    """Save thread details to a file for debugging."""
    thread_result = thread_store.get(thread_id)
    if isinstance(thread_result, Right):
        thread = thread_result.value
        
        # Create threads directory if it doesn't exist
        threads_dir = Path(thread_dir)
        threads_dir.mkdir(exist_ok=True)
        
        # Save thread details
        thread_data = {
            "thread_id": thread.id,
            "query": thread.query,
            "actions": [str(action) for action in thread.actions]
        }
        
        with open(threads_dir / f"{thread_id}.json", 'w') as f:
            json.dump(thread_data, f, indent=2)


def extract_dataset_name(dataset_path: str) -> str:
    """Extract dataset name from the file path."""
    # Get the filename without extension
    # e.g., "evals/simple_tasks.yaml" -> "simple_tasks"
    return Path(dataset_path).stem


def generate_datetime_string() -> str:
    """Generate datetime string in format YYYYMMDD-HHMM."""
    now = datetime.now()
    return now.strftime("%Y%m%d-%H%M")


def generate_report_filename(driver: str, dataset_path: str) -> str:
    """Generate descriptive filename for evaluation report."""
    dataset_name = extract_dataset_name(dataset_path)
    datetime_str = generate_datetime_string()
    return f"{driver}-{dataset_name}-{datetime_str}.json"


def create_results_table(results: list[EvaluationResult]) -> Table:
    """Create a rich table displaying evaluation results."""
    table = Table(title="Evaluation Results", show_lines=True)
    
    table.add_column("Test ID", style="cyan", no_wrap=True)
    table.add_column("Task ✓", justify="center", style="green")
    table.add_column("Result ✓", justify="center", style="green")
    table.add_column("Steps ✓", justify="center", style="green")
    table.add_column("Actions ✓", justify="center", style="green")
    table.add_column("Status", style="bold")
    
    for result in results:
        # Use icons for each subscore
        task_icon = "✅" if result.task_completed else "❌"
        result_icon = "✅" if result.result_valid else "❌"
        steps_icon = "✅" if result.step_count_match else "❌"
        actions_icon = "✅" if result.expected_actions_found else "❌"
        
        # Overall status
        all_passed = all([
            result.task_completed,
            result.result_valid,
            result.step_count_match,
            result.expected_actions_found
        ])
        status = "[green]PASS[/green]" if all_passed else "[red]FAIL[/red]"
        
        table.add_row(
            result.test_id,
            task_icon,
            result_icon,
            steps_icon,
            actions_icon,
            status
        )
    
    return table


def create_summary_panel(
    results: list[EvaluationResult], driver: str, dataset_name: str
) -> Panel:
    """Create a summary panel with evaluation statistics."""
    total_tests = len(results)
    
    task_completed = sum(1 for r in results if r.task_completed)
    result_valid = sum(1 for r in results if r.result_valid)
    step_count_match = sum(1 for r in results if r.step_count_match)
    expected_actions_found = sum(1 for r in results if r.expected_actions_found)
    
    # Calculate pass rate
    all_passed = sum(1 for r in results if all([
        r.task_completed,
        r.result_valid,
        r.step_count_match,
        r.expected_actions_found
    ]))
    pass_rate = (all_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Calculate percentages
    task_pct = task_completed / total_tests * 100
    result_pct = result_valid / total_tests * 100
    step_pct = step_count_match / total_tests * 100
    actions_pct = expected_actions_found / total_tests * 100
    
    # Determine pass rate color
    if pass_rate >= 80:
        pass_color = "green"
    elif pass_rate >= 60:
        pass_color = "yellow"
    else:
        pass_color = "red"
    
    pass_rate_text = f"({pass_rate:.1f}%)"
    
    summary_text = f"""
[bold]Driver:[/bold] {driver}
[bold]Dataset:[/bold] {dataset_name}
[bold]Total Tests:[/bold] {total_tests}

[bold]Results:[/bold]
  • Task Completed: {task_completed}/{total_tests} ({task_pct:.1f}%)
  • Result Valid: {result_valid}/{total_tests} ({result_pct:.1f}%)
  • Step Count Match: {step_count_match}/{total_tests} ({step_pct:.1f}%)
  • Expected Actions Found: {expected_actions_found}/{total_tests} ({actions_pct:.1f}%)

[bold]Overall Pass Rate:[/bold] {all_passed}/{total_tests} ([{pass_color}]{pass_rate_text}[/])
"""
    
    return Panel(
        summary_text.strip(),
        title="📊 Evaluation Summary",
        border_style="blue",
        padding=(1, 2)
    )


def run_evaluation(
    dataset_path: str,
    driver: str,
    report_dir: str = ".",
    thread_dir: str = "eval_threads",
) -> int:
    """Run evaluation on a dataset."""
    load_dotenv()
    console = Console()
    
    # Set the active driver
    try:
        Config.set_driver(driver)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1
    
    # Load dataset
    try:
        test_cases = load_dataset(dataset_path)
    except Exception as e:
        console.print(f"[red]Error loading dataset: {e}[/red]")
        return 1
    
    dataset_name = extract_dataset_name(dataset_path)
    
    # Show initial header
    console.print("\n[bold blue]🧪 Running Evaluation[/bold blue]")
    console.print(f"[cyan]Dataset:[/cyan] {dataset_name}")
    console.print(f"[cyan]Driver:[/cyan] {driver}")
    console.print(f"[cyan]Test Cases:[/cyan] {len(test_cases)}")
    console.print()
    
    results = []
    
    # Run evaluation with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task(
            "Running evaluation...",
            total=len(test_cases)
        )
        
        for _i, test_case in enumerate(test_cases, 1):
            progress.update(task, description=f"Running {test_case.id}...")
            
            start_time = time.time()
            result, thread_store = evaluate_test_case(test_case, driver)
            end_time = time.time()
            
            results.append(result)
            
            # Save thread details for debugging
            save_thread_details(result.thread_id, thread_store, thread_dir)
            
            # Update progress
            progress.update(task, advance=1)
            
            # Show quick status for this test
            status = "✅ PASS" if all([
                result.task_completed,
                result.result_valid,
                result.step_count_match,
                result.expected_actions_found
            ]) else "❌ FAIL"
            
            console.print(f"  {test_case.id}: {status} ({end_time - start_time:.1f}s)")
    
    console.print()
    
    # Display results table
    results_table = create_results_table(results)
    console.print(results_table)
    console.print()
    
    # Display summary panel
    summary_panel = create_summary_panel(results, driver, dataset_name)
    console.print(summary_panel)
    
    # Save detailed JSON report
    report_data = {
        "dataset_path": dataset_path,
        "driver": driver,
        "total_tests": len(test_cases),
        "summary": {
            "task_completed": sum(1 for r in results if r.task_completed),
            "result_valid": sum(1 for r in results if r.result_valid),
            "step_count_match": sum(1 for r in results if r.step_count_match),
            "expected_actions_found": sum(
                1 for r in results if r.expected_actions_found
            ),
        },
        "results": [
            {
                "test_id": r.test_id,
                "thread_id": r.thread_id,
                "task_completed": r.task_completed,
                "result_valid": r.result_valid,
                "step_count_match": r.step_count_match,
                "expected_actions_found": r.expected_actions_found,
                "actual_result": r.actual_result,
                "actual_steps": r.actual_steps,
                "error_message": r.error_message
            }
            for r in results
        ]
    }
    
    # Save report with descriptive filename
    report_filename = generate_report_filename(driver, dataset_path)
    report_path = Path(report_dir) / report_filename
    
    # Create report directory if it doesn't exist
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Show final status
    console.print()
    console.print(
        f"📄 [bold green]Report saved to:[/bold green] [cyan]{report_path}[/cyan]"
    )
    thread_text = f"🧵 [bold green]Thread details saved to:[/bold green] [cyan]{thread_dir}/[/cyan]"
    console.print(thread_text)
    
    return 0