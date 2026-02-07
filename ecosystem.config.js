module.exports = {
  apps: [
    {
      name: 'technical-analysis-api',
      script: './src/main.py',
      interpreter: 'python3',
      interpreter_args: '-u',
      cwd: '/opt/technical_analysis_helper',
      instances: 1,
      exec_mode: 'fork',
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_file: './logs/pm2-combined.log',
      time: true,
      merge_logs: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '500M',
      watch: false,
      ignore_watch: [
        'node_modules',
        'logs',
        '.git',
        '__pycache__',
        '*.pyc',
        '.pytest_cache'
      ]
    }
  ]
};
