# Documentation Assets

PNG screenshots are omitted from version control to keep the repository binary-free. To obtain the example dashboard screenshot:

1. Bring the stack online:
   ```bash
   cp .env.example .env
   docker compose up -d
   ```
2. Open Grafana at http://127.0.0.1:3000 and log in with the credentials configured in your `.env` file.
3. Navigate to **Dashboards → Browse → 01 Overview**.
4. Select the **Share** button in the upper-right corner, choose **Export**, and click **Download PNG**.
5. Save the file to `docs/images/overview-dashboard.png` (create the `docs/images` directory if needed).

This keeps documentation reproducible while allowing you to maintain local screenshots when desired.
