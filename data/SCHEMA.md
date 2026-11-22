# Site Schema

Each entry in `sites.json` should follow:

```json
{
  "name": "string (required)",
  "url": "string (required, absolute)",
  "category": "string (directory|search|proxy|news|weather|archive|classic|community|reference|other)",
  "description": "string",
  "text_friendly": true,
  "tags": ["array of strings"],
  "last_checked": "YYYY-MM-DD (optional)",
  "status": "ok|down|redirect|unknown (optional)",
  "notes": "string (optional)"
}
```

Prefer sites that:
- Work without JavaScript
- Have useful content in pure HTML / text
- Are low-bandwidth
- Are useful to Lynx / retro / BBS users
