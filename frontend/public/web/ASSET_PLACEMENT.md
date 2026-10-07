# Web asset placement

Copy favicons and icons into `apps/web/public/brand/`. In a Next.js App Router project, either reference those files from metadata or copy the preferred icon to `apps/web/src/app/icon.png` and the favicon to `apps/web/src/app/favicon.ico`.

Authored marketing images belong in `apps/web/public/images/`. User uploads do not belong in the repository or public folder; send them through the backend to S3-compatible storage and store only metadata and authorization policy in PostgreSQL.
