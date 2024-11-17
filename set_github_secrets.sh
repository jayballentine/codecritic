#!/bin/bash

# Read .env.test file
source .env.test

# Set GitHub repository secrets with modified names
gh secret set CLIENT_ID --body "$GITHUB_CLIENT_ID"
gh secret set CLIENT_SECRET --body "$GITHUB_CLIENT_SECRET"
gh secret set HOMEPAGE_URL --body "$GITHUB_HOMEPAGE_URL"
gh secret set REDIRECT_URI --body "$GITHUB_REDIRECT_URI"
gh secret set WEBHOOK_URL --body "$GITHUB_WEBHOOK_URL"
gh secret set PERSONAL_ACCESS_TOKEN --body "$GITHUB_PAT"

# Other secrets remain unchanged
gh secret set SUPABASE_URL --body "$SUPABASE_URL"
gh secret set SUPABASE_KEY --body "$SUPABASE_KEY"
gh secret set SENDGRID_API_KEY --body "$SENDGRID_API_KEY"
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"
gh secret set ANTHROPIC_API_KEY --body "$ANTHROPIC_API_KEY"
gh secret set JWT_SECRET_KEY --body "$JWT_SECRET_KEY"

echo "All secrets have been set successfully."
