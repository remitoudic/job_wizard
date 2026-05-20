<script>
	import { fade } from 'svelte/transition';
	import SEO from '$lib/components/SEO.svelte';
</script>

<SEO
	title="Privacy Policy - Vite a Job"
	description="Learn how Vite a Job protects your personal data and privacy. Our policy details the collection, use, and security of your information on our platform."
	canonical="https://viteajob.com/privacy"
/>

<div class="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8" in:fade={{ duration: 300 }}>
	<div class="bg-white shadow-xl rounded-2xl overflow-hidden border border-slate-100">
		<div class="p-8 sm:p-12">
			<h1 class="text-3xl font-bold text-slate-900 mb-8">Privacy Policy</h1>

			<div class="prose prose-slate max-w-none text-slate-700">
				<p class="text-sm text-slate-500 mb-6">
					Last updated: {new Date().toLocaleDateString()}
				</p>

				<p>
					At Vite a Job "we", we value your privacy and are committed to protecting your personal
					information. This Privacy Policy explains how we collect, use, and safeguard your data
					when you use our job application optimization service.
				</p>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">1. Information We Collect</h2>
				<ul class="list-disc pl-5 space-y-2 mb-4">
					<li>
						<strong>Personal Information:</strong> When you register, we collect information such as your
						name and email address.
					</li>
					<li>
						<strong>User Content:</strong> We store the job descriptions, resumes, and cover letters you
						upload or generate to provide our services.
					</li>
					<li>
						<strong>Usage Data:</strong> We collect data on how you interact with our service to improve
						performance and user experience.
					</li>
				</ul>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
					2. How We Use Your Information
				</h2>
				<p>We use your information to:</p>
				<ul class="list-disc pl-5 space-y-2 mb-4">
					<li>Provide and maintain our Service.</li>
					<li>Generate personalized cover letters and analyze job postings.</li>
					<li>Improve our algorithms and user interface.</li>
					<li>Communicate with you about your account and service updates.</li>
				</ul>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">3. Data Security</h2>
				<p>
					We implement industry-standard security measures to protect your data. However, no method
					of transmission over the Internet or electronic storage is 100% secure, and we cannot
					guarantee absolute security.
				</p>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">4. Sharing Your Information</h2>
				<p>
					We do not sell your personal data. We may share data with third-party service providers
					(e.g., cloud hosting, AI providers) solely for the purpose of operating our Service.
				</p>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">5. Your Rights</h2>
				<p>
					You have the right to access, correct, or delete your personal information. You can manage
					your data directly within your account settings or contact us for assistance.
				</p>

				<h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">6. Contact Us</h2>
				<p>
					If you have any questions about this Privacy Policy, please contact us at
					remitoudic@gmail.com.
				</p>
			</div>
		</div>
	</div>
</div>
