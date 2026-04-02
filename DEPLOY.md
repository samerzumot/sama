# How to Deploy Sama

You can deploy this website to Vercel using one of the following methods.

## Option 1: Vercel CLI (Recommended)

1.  Open your terminal.
2.  Navigate to the project directory:
    ```bash
    cd /Users/zumot/Sama
    ```
3.  Run the deploy command **with a new project name**:
    ```bash
    vercel
    ```
4.  Follow the interactive prompts EXACTLY as below:
    - Set up and deploy? [Y/n] **Y**
    - Which scope do you want to deploy to? (Select your team/account)
    - Link to existing project? [y/N] **N**  <-- **CRITICAL: Say N here**
    - What’s your project’s name? **sama-web** (or any unique name, DO NOT use "sama")
    - In which directory is your code located? **./**
    - Want to modify these settings? [y/N] **N**

5.  Once completed, it will give you a **Production** URL.

## Option 2: Vercel Dashboard (Git)

1.  Push your code to a Git repository.
2.  In Vercel, create a **New Project**.
3.  Import your repo.
4.  **Important**: Ensure `Framework Preset` is set to **Other**.
