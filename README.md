# Agent Skills

This repository contains reusable agent skills for a variety of development tasks across different tools and workflows.

## Installation

To install skills from this repository, run:

```bash
npx skills add hukusuke1007/agent-skills
```

## Updating Skills

To update installed skills from this repository, run:

```bash
npx skills update hukusuke1007/agent-skills
```

## Available Skills

| Skill                                                                                 | Description                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`flutter-riverpod-arch`](./flutter-riverpod-arch/SKILL.md)                           | Implement Feature-First Flutter architecture with Riverpod (code generation), Flutter Hooks, layered responsibilities (UI → Use Case → Repository), and testing patterns.                                           |
| [`nextjs-better-auth-postgres-docker`](./nextjs-better-auth-postgres-docker/SKILL.md) | Build and deploy a Next.js (App Router) + Better Auth + PostgreSQL app using Docker locally, and deploy to Google Cloud Run with Cloud SQL and Secret Manager. **Written in Japanese.**                             |
| [`meti-ai-guideline`](./meti-ai-guideline/SKILL.md)                                   | Answer OK/NG judgments, checklists, and guidance based on Japan's AI Business Operator Guidelines (経済産業省・総務省 AI事業者ガイドライン). Supports AI developers, providers, and users. **Written in Japanese.** |
| [`nano-banana-image-gen`](./nano-banana-image-gen/SKILL.md)                           | Generate images using Google Gemini (`gemini-2.0-flash-preview-image-generation`). Outputs timestamped PNGs to `0_images/generated/`. Requires a Gemini API key. **Written in Japanese.**                           |

## Setup Notes

### meti-ai-guideline

The `references/` directory is **not included** in this repository due to copyright. You need to download the PDFs from METI and set them up manually.

1. Download the following PDFs from the [METI page](https://www.meti.go.jp/shingikai/mono_info_service/ai_shakai_jisso/20260331_report.html):
   - AI事業者ガイドライン (Main document)
   - AI事業者ガイドライン活用の手引き (Usage guide)
   - AI事業者ガイドライン チェックリスト 別添7 (Checklist)

2. Extract text using `pdftotext` and place the files as follows:

   ```
   meti-ai-guideline/references/
   ├── common_guidelines.md
   ├── ai_developer.md
   ├── ai_provider.md
   ├── ai_user.md
   ├── checklist.md
   └── usage_guide.md
   ```

3. Add the source attribution at the top of each file:

   ```
   出典: AI事業者ガイドライン（第X.X版）総務省・経済産業省, YYYY年MM月DD日
   ```

### nano-banana-image-gen

Requires a Google Gemini API key. Add the following to your `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
GENERATED_IMAGE_OUTPUT_PATH=images/generated
```

Install dependencies:

```bash
pip install google-genai pillow python-dotenv
```

#### Security Note: Protecting `.env` from AI

AI coding tools (Claude Code, Cursor, etc.) may automatically read `.env` files and send the contents — including API keys — to LLM providers. To prevent this, add the following to your `settings.json`:

```json
// .claude/settings.json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(.env.*)"
    ]
  }
}
```

Also add `.env` to `.gitignore` to avoid accidentally committing secrets:

```
# .gitignore
.env
.env.*
!.env.sample
```

## References

- [https://agentskills.io](https://agentskills.io)
- [https://github.com/anthropics/skills](https://github.com/anthropics/skills)
- [https://github.com/vercel-labs/skills](https://github.com/vercel-labs/skills)
- [https://github.com/flutter/skills](https://github.com/flutter/skills)
- [https://skills.sh](https://skills.sh)

## Contributing

Issues and pull requests are welcome for new skills, improvements, and fixes.

## License

This repository is licensed under the [MIT License](./LICENSE).
