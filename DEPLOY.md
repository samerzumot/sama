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

## Stripe Environment Variables

Before your payments will work on the production site, you **must** add your Stripe Secret Key to Vercel:

1. Go to your **Vercel Dashboard**.
2. Select your project (**sama-web**).
3. Go to **Settings > Environment Variables**.
4. Add a new variable:
   - **Key**: `STRIPE_SECRET_KEY`
   - **Value**: `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`
5. Click **Save** and redeploy the project for the settings to take effect.
