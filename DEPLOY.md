# Deployment Guide to GitHub

Follow these steps to deploy your project to GitHub.

## Prerequisite
Ensure you have a GitHub account and have created a **new empty repository** (do not initialize it with README/gitignore, we already have those).

## Steps

1.  **Initialize Git**:
    Open your terminal in the project folder and run:
    ```bash
    git init
    ```

2.  **Add Files**:
    Stage all your files (our `.gitignore` will ensure only the right files are added):
    ```bash
    git add .
    ```

3.  **Commit**:
    Save your changes:
    ```bash
    git commit -m "Initial commit of Geospatial Agent"
    ```

4.  **Link to GitHub**:
    Replace `<YOUR_REPO_URL>` with the URL of the repository you created on GitHub (e.g., `https://github.com/username/repo.git`).
    ```bash
    git remote add origin <YOUR_REPO_URL>
    ```

5.  **Push**:
    Upload your code:
    ```bash
    git push -u origin main
    ```

## Notes
-   Your **API Keys** in `.env` are ignored and will NOT be uploaded. You must set them manually in your deployment environment if you move this elsewhere.
-   The large datasets in `data/` are ignored to save space, except for `synthetic_houses.geojson` which is included for demo purposes.
