<script>
    import { fade } from "svelte/transition";
    import SEO from "$lib/components/SEO.svelte";
</script>

<SEO
    title="Terms of Service - Vite a Job"
    description="Read the terms and conditions for using Vite a Job. Understand your rights, responsibilities, and our service guarantees when using our AI tools."
    canonical="https://viteajob.com/terms"
/>

<div
    class="max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8"
    in:fade={{ duration: 300 }}
>
    <div
        class="bg-white shadow-xl rounded-2xl overflow-hidden border border-slate-100"
    >
        <div class="p-8 sm:p-12">
            <h1 class="text-3xl font-bold text-slate-900 mb-8">
                Terms of Service
            </h1>

            <div class="prose prose-slate max-w-none text-slate-700">
                <p class="text-sm text-slate-500 mb-6">
                    Last updated: {new Date().toLocaleDateString()}
                </p>

                <p>
                    Welcome to Vite a Job. By accessing or using our website and
                    services, you agree to be bound by these Terms of Service.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    1. Service Description
                </h2>
                <p>
                    Vite a Job is a SaaS platform that uses AI to help users
                    optimize their job applications, including generating cover
                    letters and analyzing job descriptions.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    2. User Accounts
                </h2>
                <ul class="list-disc pl-5 space-y-2 mb-4">
                    <li>
                        You must provide accurate and complete information when
                        creating an account.
                    </li>
                    <li>
                        You are responsible for safeguarding your account
                        credentials.
                    </li>
                    <li>
                        We reserve the right to suspend or terminate accounts
                        that violate these terms.
                    </li>
                </ul>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    3. Acceptable Use
                </h2>
                <p>You agree not to:</p>
                <ul class="list-disc pl-5 space-y-2 mb-4">
                    <li>Use the service for any illegal purpose.</li>
                    <li>Attempt to reverse engineer or scrape our platform.</li>
                    <li>
                        Generate content that is harmful, offensive, or violates
                        third-party rights.
                    </li>
                </ul>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    4. Intellectual Property
                </h2>
                <p>
                    The service and its original content, features, and
                    functionality are owned by Vite a Job and are protected by
                    international copyright, trademark, and other intellectual
                    property laws.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    5. Disclaimer of Warranties
                </h2>
                <p>
                    The service is provided on an "AS IS" and "AS AVAILABLE"
                    basis. We do not warrant that the results generated will
                    guarantee job interviews or employment offers.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    6. Limitation of Liability
                </h2>
                <p>
                    In no event shall Vite a Job be liable for any indirect,
                    incidental, special, consequential, or punitive damages
                    arising out of or relating to your use of the service.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    7. Changes to Terms
                </h2>
                <p>
                    We reserve the right to modify these terms at any time. We
                    will provide notice of any material changes via email or a
                    prominent notice on our service.
                </p>

                <h2 class="text-xl font-semibold text-slate-900 mt-8 mb-4">
                    8. Contact
                </h2>
                <p>
                    If you have any questions about these Terms, please contact
                    us at remitoudic@gmail.com.
                </p>
            </div>
        </div>
    </div>
</div>
