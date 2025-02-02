# tfe-tools
Tools for interacting with TFE Api

## GitHub Actions Workflow for Running Python Tests

This repository includes a GitHub Actions workflow to run Python tests. The workflow is triggered on the following events:
- `push`
- `workflow_dispatch`
- `pull_request`

The workflow sets up a Python environment, installs dependencies from `requirements.txt`, and runs the tests using `pytest`.

### Manually Triggering the Workflow

To manually trigger the workflow, follow these steps:
1. Go to the "Actions" tab in your GitHub repository.
2. Select the "Python Tests" workflow from the list of workflows.
3. Click on the "Run workflow" button.
4. Choose the branch on which you want to run the workflow.
5. Click on the "Run workflow" button to start the workflow.
