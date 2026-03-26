# SEO & GEO Strategy Guide

This document outlines the SEO (Search Engine Optimization) and GEO (Generative Engine Optimization) strategy implemented for Vite a Job.

## 🏗 Architecture

The SEO system is built around the `SEO.svelte` component (`frontend/src/lib/components/SEO.svelte`).

### Key Features:
1. **Dynamic Metadata**: Handles `<title>`, `<meta description>`, and canonical URLs per page.
2. **Social Graph**: Automatically generates Open Graph (LinkedIn/Facebook) and Twitter Card tags.
3. **Structured Data (JSON-LD)**: Implements `SoftwareApplication` schema for Google and AI agents.
4. **Keyword Shielding**: Base meta tags in `app.html` provide a safety net for any routes without a specific SEO component.

## 🚀 Keyword Targeting Strategy

Our current primary target keyword is: **"how to write a cover letter"**.

### Implementation:
- **Landing Page**: Meta description leads with the keyword.
- **Why Page**: Contains a dedicated educational section ("Expert Guide: How to Write a Cover Letter that Beats the ATS") providing the value search engines look for.
- **Schema**: The `SoftwareApplication` is sub-categorized as a "how to write a cover letter guide".

## 🤖 GEO (Generative Engine Optimization)

To improve visibility in AI responses (ChatGPT, Claude, Perplexity), we use the following:
- **FAQ Sections**: Structured Question/Answer pairs on the `/why` page for easy citation by LLMs.
- **E-E-A-T Signals**: "Last Updated" timestamps and clear author/brand identification to demonstrate authority.
- **Semantic HTML**: Clear heading hierarchies (H1 -> H2 -> H3) to help AI parsers understand content context.

## 🛠 Developer Maintenance

When adding new pages:
1. Import and use `<SEO />` in your `+page.svelte`.
2. Provide a unique, keyword-rich description (150-160 characters).
3. Set the `canonical` prop to the full URL.

To update the sitemap, modify `frontend/src/routes/sitemap.xml/+server.js`.
To change crawl rules, modify `frontend/static/robots.txt`.
