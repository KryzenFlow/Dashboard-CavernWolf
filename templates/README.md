# Hermes template packs (ClaudexApp / Doex workflows)

| Template ID | Folder | Stack | Target customer |
|-------------|--------|-------|-----------------|
| `static-site` | `static-site/` | HTML/CSS, Vite-ready | Freelancers, portfolios |
| `landing-page` | `landing-page/` | Landing page | Small businesses |
| `react-app` | `react-app/` | React + npm | Internal dashboards, SMEs |

## Scaffold via CLI

```bash
docker compose exec dev-tools hermes-cli new site --template static-site --name mysite
```

## Scaffold via Hermes Studio

Projects tab → **New Website**

## Workflow JSON example

See `shared/workflows/example-workflow.json`
