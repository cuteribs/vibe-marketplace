#!/usr/bin/env node

/**
 * Feishu Notification Hook
 * Sends status updates to Feishu (enterprise collaboration platform)
 *
 * Usage: node feishu_notify.js --text "Message" [--webhook <url>]
 *
 * Configuration:
 * Set FEISHU_WEBHOOK_URL environment variable
 */

const https = require('https');
const url = require('url');

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  const result = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--text' && i + 1 < args.length) {
      result.text = args[i + 1];
      i++;
    } else if (args[i] === '--webhook' && i + 1 < args.length) {
      result.webhook = args[i + 1];
      i++;
    }
  }

  return result;
}

// Get webhook URL from environment variable
function getWebhookUrl() {
  return process.env.FEISHU_WEBHOOK_URL;
}

// Send notification to Feishu
function sendNotification(webhookUrl, text) {
  return new Promise((resolve, reject) => {
    const payload = {
      msg_type: 'text',
      content: {
        text: `[Claude Code] ${text}`
      }
    };

    const parsedUrl = new url.URL(webhookUrl);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 443,
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(JSON.stringify(payload))
      }
    };

    const req = https.request(options, (res) => {
      let data = '';

      res.on('data', chunk => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.code === 0) {
            resolve(true);
          } else {
            reject(new Error(`Feishu API error: ${response.msg}`));
          }
        } catch (err) {
          reject(err);
        }
      });
    });

    req.on('error', reject);
    req.write(JSON.stringify(payload));
    req.end();
  });
}

async function main() {
  try {
    const args = parseArgs();

    if (!args.text) {
      console.error('Error: --text parameter is required');
      process.exit(1);
    }

    const webhookUrl = args.webhook || getWebhookUrl();

    if (!webhookUrl) {
      // Silently skip if no webhook is configured
      // This allows the hook to be installed without a webhook set up
      process.exit(0);
    }

    await sendNotification(webhookUrl, args.text);
    process.exit(0);
  } catch (err) {
    console.error('Feishu notification failed:', err.message);
    // Don't fail the hook - this is non-critical
    process.exit(0);
  }
}

main();
