# Deploying to Railway

This guide will help you deploy the bot to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. A GitHub account (to connect your repository)

## Deployment Steps

### 1. Prepare Your Repository

Make sure all files are committed to Git:
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### 2. Create a New Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the project

### 3. Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

- `PORT` - Railway will set this automatically, but you can verify it's there
- `FLASK_ENV=production` - Set to production mode
- `RAILWAY_ENVIRONMENT=production` - Enable headless mode

### 4. Deploy

Railway will automatically:
- Install dependencies from `requirements.txt`
- Install Chrome and ChromeDriver (via nixpacks.toml)
- Start the application using the Procfile

### 5. Access Your Bot

Once deployed, Railway will provide a URL like:
`https://your-app-name.up.railway.app`

You can access the bot UI at this URL.

## Important Notes

### Chrome/ChromeDriver
- Railway will install Chrome and ChromeDriver automatically via nixpacks.toml
- The bot runs in headless mode on Railway (no GUI)

### OCR (EasyOCR)
- First run will download model files (~100MB)
- This may take a few minutes on first startup
- Models are cached for subsequent runs

### Data Persistence
- Screenshots and CSV files are stored in the `data/` directory
- These files are ephemeral on Railway (will be lost on redeploy)
- Consider using Railway volumes or external storage for persistence

### Manual Login
- Users will need to log in manually through the browser
- The bot waits for manual login before starting monitoring

## Troubleshooting

### Bot won't start
- Check Railway logs for errors
- Verify Chrome/ChromeDriver installation
- Check if OCR models are downloading correctly

### Screenshots not saving
- Verify `data/` directory has write permissions
- Check Railway logs for file system errors

### Port errors
- Railway automatically sets the PORT environment variable
- The app.py is configured to use this port

## Monitoring

- Check Railway logs: Project → Deployments → View Logs
- Monitor resource usage in Railway dashboard
- Set up alerts for crashes or high resource usage

## Updating

To update your bot:
1. Push changes to GitHub
2. Railway will automatically redeploy
3. Monitor logs to ensure successful deployment

