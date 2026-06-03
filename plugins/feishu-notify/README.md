# Feishu Notify Plugin

A Claude Code plugin that integrates with Feishu (enterprise collaboration platform) to send status notifications about Claude Code activities.

## Features

- Sends notifications on various Claude Code events:
  - Notification requests
  - Permission requests
  - Session end events
  - Idle stops
  - Subagent starts
  - User prompt submissions
  - Tool usage events

## Installation

1. Copy this plugin to your Claude Code plugins directory
2. Configure your Feishu webhook URL (see Configuration section below)
3. Restart Claude Code

## Configuration

Set the `FEISHU_WEBHOOK_URL` environment variable:

```bash
export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_KEY"
```

## Getting Your Webhook URL

1. Go to your Feishu workspace
2. Create a new bot or use an existing one
3. Add webhook integration
4. Copy the webhook URL
5. Add it to your configuration (Option 1 or 2 above)

## How It Works

The plugin sets up hooks in your Claude Code configuration that trigger when specific events occur:

- **PreToolUse**: Triggered before Claude uses any tool
- **UserPromptSubmit**: Triggered when you submit a prompt
- **PermissionRequest**: Triggered when Claude Code requests permission for an action
- **Notification**: Triggered for notifications
- **Stop**: Triggered when Claude Code stops (idle)
- **SessionEnd**: Triggered when your session ends
- **SubagentStart**: Triggered when a subagent starts

Each event sends a formatted message to your Feishu workspace.

## Message Format

Messages are sent in the following format:

```
[Claude Code] <event message>
```

Examples:
- `[Claude Code] Busy PreToolUse`
- `[Claude Code] Session Ended`
- `[Claude Code] Waiting Permission Request`

## Troubleshooting

- **No messages appearing**: Ensure your webhook URL is correct and Feishu bot is active
- **Script not found**: Verify the plugin is properly installed in the plugins directory
- **Permission denied**: Ensure the `feishu_notify.js` script is executable

## Files

- `plugin.json` - Plugin manifest with hook definitions
- `scripts/feishu_notify.js` - Main notification script
- `README.md` - This file

## Version

1.0.0

## License

MIT
