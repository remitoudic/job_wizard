<script lang="ts">
	export let title: string = 'Vite a Job - AI Cover Letter Generator';
	export let description: string =
		'Create professional, AI-optimized cover letters in seconds. Beat the ATS filters and get more interviews with our intelligent job application generator.';
	export let image: string = 'https://viteajob.com/images/og-main.png';
	export let type: string = 'website';
	export let canonical: string = 'https://viteajob.com';
	export let schema: any = {
		'@context': 'https://schema.org',
		'@type': 'SoftwareApplication',
		name: 'Vite a Job',
		operatingSystem: 'Web',
		applicationCategory: 'BusinessApplication',
		applicationSubCategory: 'how to write a cover letter guide',
		offers: {
			'@type': 'Offer',
			price: '0.00',
			priceCurrency: 'USD'
		},
		description:
			'AI-powered cover letter generator designed to help job seekers bypass ATS filters and personalize their applications.'
	};

	const siteName = 'Vite a Job';
</script>

<svelte:head>
	<!-- Primary Meta Tags -->
	<title>{title}</title>
	<meta name="title" content={title} />
	<meta name="description" content={description} />
	<link rel="canonical" href={canonical} />

	<!-- Open Graph / Facebook / LinkedIn -->
	<meta property="og:type" content={type} />
	<meta property="og:url" content={canonical} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content={image} />
	<meta property="og:site_name" content={siteName} />

	<!-- Twitter -->
	<meta property="twitter:card" content="summary_large_image" />
	<meta property="twitter:url" content={canonical} />
	<meta property="twitter:title" content={title} />
	<meta property="twitter:description" content={description} />
	<meta property="twitter:image" content={image} />

	<!-- Schema.org JSON-LD -->
	{#if schema}
		<!-- prettier-ignore -->
		<script type="application/ld+json">
			{@html JSON.stringify(schema)}
		</script>
	{/if}
</svelte:head>
