<script lang="ts">
    import { onMount } from "svelte";
    import { getProfile, updateProfile, uploadProfilePicture, deleteProfilePicture } from "$lib/api";
    import { auth } from "../../stores/auth";
    import type { User } from "../../stores/auth";
    import { get } from "svelte/store";
    import Cropper from "cropperjs";
    import "cropperjs/dist/cropper.css";

    // SvelteKit may pass `data` and `params` to pages — declare to prevent runtime warnings
    export let data: any = {};
    export let params: Record<string, string> = {};

    let user: User | null = null;
    let isLoading = true;
    let isSaving = false;
    let isAddressOpen = false;
    let message = "";
    let error = "";

    // Profile Picture logic
    let fileInput: HTMLInputElement;
    let imageToCrop: string | null = null;
    let cropperRef: HTMLImageElement;
    let cropperInstance: Cropper | null = null;
    let isUploading = false;
    let isDeleting = false;

    function handleFileSelect(event: Event) {
        const file = (event.target as HTMLInputElement).files?.[0];
        if (!file) return;

        // Reset file input
        fileInput.value = '';

        const reader = new FileReader();
        reader.onload = (e) => {
            imageToCrop = e.target?.result as string;
            // Initialize cropper after tick
            setTimeout(() => {
                if (cropperRef) {
                    cropperInstance = new Cropper(cropperRef, {
                        aspectRatio: 1,
                        viewMode: 1,
                        dragMode: 'move',
                        autoCropArea: 0.8,
                        restore: false,
                        guides: false,
                        center: false,
                        highlight: false,
                        cropBoxMovable: true,
                        cropBoxResizable: true,
                        toggleDragModeOnDblclick: false,
                    });
                }
            }, 0);
        };
        reader.readAsDataURL(file);
    }

    function cancelCrop() {
        if (cropperInstance) {
            cropperInstance.destroy();
            cropperInstance = null;
        }
        imageToCrop = null;
    }

    async function handleCropSave() {
        if (!cropperInstance || !user) return;
        
        isUploading = true;
        try {
            const canvas = cropperInstance.getCroppedCanvas({
                width: 400,
                height: 400,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high',
            });
            
            canvas.toBlob(async (blob: Blob | null) => {
                if (!blob) {
                    error = "Failed to export cropped image";
                    isUploading = false;
                    return;
                }
                
                try {
                    const token = get(auth).token;
                    if (!token) throw new Error("No token");
                    
                    const updatedUser = await uploadProfilePicture(token, blob);
                    user = updatedUser;
                    auth.updateUser(user);
                    message = "Profile picture updated successfully!";
                    cancelCrop();
                } catch (err: any) {
                    error = err.message || "Failed to upload image";
                } finally {
                    isUploading = false;
                }
            }, 'image/jpeg', 0.9);
            
        } catch (err) {
            error = "Failed to process image";
            isUploading = false;
        }
    }

    async function handleDeletePicture() {
        if (!user || !user.profile_picture_url) return;
        if (!confirm("Are you sure you want to delete your profile picture?")) return;
        
        isDeleting = true;
        try {
            const token = get(auth).token;
            if (!token) throw new Error("No token");
            
            const updatedUser = await deleteProfilePicture(token);
            user = updatedUser;
            auth.updateUser(user);
            message = "Profile picture deleted successfully!";
        } catch (err: any) {
            error = err.message || "Failed to delete image";
        } finally {
            isDeleting = false;
        }
    }

    onMount(async () => {
        try {
            user = await getProfile();
            auth.updateUser(user!);
        } catch (e) {
            error = "Failed to load profile";
        } finally {
            isLoading = false;
        }
    });

    async function handleSave() {
        if (!user) return;
        isSaving = true;
        message = "";
        error = "";

        try {
            const updatedUser = await updateProfile(user);
            user = updatedUser;
            auth.updateUser(user!);
            message = "Profile updated successfully!";
        } catch (e: any) {
            error = e.message || "Failed to update profile";
        } finally {
            isSaving = false;
        }
    }
</script>

<div
    class="max-w-2xl mx-auto mt-8 p-6 bg-white rounded-lg shadow-md border border-gray-100"
>
    <h1 class="text-2xl font-bold mb-6 text-gray-800">My Profile</h1>

    <div
        class="mb-6 p-4 bg-blue-50 text-blue-800 rounded-lg text-sm border border-blue-100 flex items-start gap-3"
    >
        <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 text-blue-500 mt-0.5 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
        </svg>
        <p>
            The contact information will be used for the header of covering
            letter, and will be used only for this purpose.
        </p>
    </div>

    {#if isLoading}
        <div class="text-center py-10 text-gray-500">Loading profile...</div>
    {:else if user}
        {#if message}
            <div
                class="mb-4 p-3 bg-green-50 text-green-700 rounded text-sm border border-green-200"
            >
                {message}
            </div>
        {/if}
        {#if error}
            <div
                class="mb-4 p-3 bg-red-50 text-red-600 rounded text-sm border border-red-200"
            >
                {error}
            </div>
        {/if}

        <!-- Profile Picture Section -->
        <div class="mb-8 flex flex-col sm:flex-row items-center sm:items-start gap-6 pb-8 border-b border-gray-100">
            <div class="relative group">
                {#if user.profile_picture_url}
                    <img src={user.profile_picture_url} alt="Profile" class="w-24 h-24 rounded-full object-cover border-4 border-white shadow-md bg-gray-50" />
                {:else}
                    <div class="w-24 h-24 rounded-full bg-primary-50 text-primary-600 flex items-center justify-center text-3xl font-bold border-4 border-white shadow-md">
                        {user.first_name?.[0] || user.email[0].toUpperCase()}
                    </div>
                {/if}
            </div>
            
            <div class="flex-1 text-center sm:text-left space-y-3">
                <h3 class="text-sm font-semibold text-gray-800">Profile Picture</h3>

                <div class="flex flex-wrap items-center justify-center sm:justify-start gap-3">
                    <input type="file" accept="image/*" class="hidden" bind:this={fileInput} on:change={handleFileSelect} />
                    <button type="button" on:click={() => fileInput.click()} class="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm">
                        Upload New
                    </button>
                    {#if user.profile_picture_url}
                        <button type="button" on:click={handleDeletePicture} disabled={isDeleting} class="px-4 py-2 text-red-600 border border-transparent rounded-lg text-sm font-medium hover:bg-red-50 transition-colors disabled:opacity-50">
                            {isDeleting ? "Deleting..." : "Delete"}
                        </button>
                    {/if}
                </div>
            </div>
        </div>

        {#if imageToCrop}
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
            <div class="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
                <div class="p-4 border-b border-gray-100 flex justify-between items-center">
                    <h3 class="font-bold text-gray-800">Crop Profile Picture</h3>
                    <button on:click={cancelCrop} class="text-gray-400 hover:text-gray-600">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                <div class="p-6 bg-gray-50 flex-1 overflow-auto flex items-center justify-center">
                    <div class="w-full aspect-square relative bg-white shadow-inner max-w-[300px] mx-auto overflow-hidden">
                        <img bind:this={cropperRef} src={imageToCrop} alt="To crop" class="block max-w-full" />
                    </div>
                </div>
                
                <div class="p-4 border-t border-gray-100 flex justify-end gap-3 bg-white">
                    <button on:click={cancelCrop} class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors">
                        Cancel
                    </button>
                    <button on:click={handleCropSave} disabled={isUploading} class="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                        {#if isUploading}
                            <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Saving...
                        {:else}
                            Save Picture
                        {/if}
                    </button>
                </div>
            </div>
        </div>
        {/if}

        <form on:submit|preventDefault={handleSave} class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label
                        for="first-name"
                        class="block text-sm font-medium text-gray-700 mb-1"
                        >First Name</label
                    >
                    <input
                        id="first-name"
                        type="text"
                        bind:value={user.first_name}
                        class="input w-full"
                        placeholder="John"
                    />
                </div>
                <div>
                    <label
                        for="surname"
                        class="block text-sm font-medium text-gray-700 mb-1"
                        >Surname</label
                    >
                    <input
                        id="surname"
                        type="text"
                        bind:value={user.surname}
                        class="input w-full"
                        placeholder="Doe"
                    />
                </div>
                <div>
                    <label
                        for="email"
                        class="block text-sm font-medium text-gray-700 mb-1"
                        >Email</label
                    >
                    <input
                        id="email"
                        type="email"
                        value={user.email}
                        disabled
                        class="input w-full bg-gray-50 text-gray-500 cursor-not-allowed"
                    />
                </div>
                <div>
                    <label
                        for="phone"
                        class="block text-sm font-medium text-gray-700 mb-1"
                        >Phone</label
                    >
                    <input
                        id="phone"
                        type="text"
                        bind:value={user.phone}
                        class="input w-full"
                        placeholder="+1 234 567 8900"
                    />
                </div>
                <div class="md:col-span-2">
                    <label
                        for="linkedin"
                        class="block text-sm font-medium text-gray-700 mb-1"
                        >LinkedIn URL</label
                    >
                    <input
                        id="linkedin"
                        type="url"
                        bind:value={user.linkedin_url}
                        class="input w-full"
                        placeholder="https://linkedin.com/in/..."
                    />
                </div>

                <div class="md:col-span-2 pt-4">
                    <button
                        type="button"
                        on:click={() => (isAddressOpen = !isAddressOpen)}
                        class="flex items-center justify-between w-full text-left text-lg font-medium text-gray-900 border-b border-gray-100 pb-2 mb-4 hover:bg-gray-50 transition-colors"
                    >
                        <span>Address</span>
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-5 w-5 transform transition-transform {isAddressOpen
                                ? 'rotate-180'
                                : ''}"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M19 9l-7 7-7-7"
                            />
                        </svg>
                    </button>
                </div>

                {#if isAddressOpen}
                    <div class="md:col-span-2 contents">
                        <div class="md:col-span-2">
                            <label
                                for="street"
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Street</label
                            >
                            <input
                                id="street"
                                type="text"
                                bind:value={user.street}
                                class="input w-full"
                                placeholder="123 Main St"
                            />
                        </div>
                        <div>
                            <label
                                for="city"
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >City</label
                            >
                            <input
                                id="city"
                                type="text"
                                bind:value={user.city}
                                class="input w-full"
                                placeholder="New York"
                            />
                        </div>
                        <div>
                            <label
                                for="postcode"
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Postcode</label
                            >
                            <input
                                id="postcode"
                                type="text"
                                bind:value={user.postcode}
                                class="input w-full"
                                placeholder="10001"
                            />
                        </div>
                        <div class="md:col-span-2">
                            <label
                                for="country"
                                class="block text-sm font-medium text-gray-700 mb-1"
                                >Country</label
                            >
                            <input
                                id="country"
                                type="text"
                                bind:value={user.country}
                                class="input w-full"
                                placeholder="USA"
                            />
                        </div>
                    </div>
                {/if}
            </div>

            <div class="pt-4 border-t border-gray-100 flex justify-end">
                <button
                    type="submit"
                    disabled={isSaving}
                    class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                    {isSaving ? "Saving..." : "Save Changes"}
                </button>
            </div>
        </form>
    {:else}
        <div class="text-center py-10">
            <p class="text-gray-500 mb-4">
                You need to be logged in to view this page.
            </p>
            <a href="/login" class="text-primary-600 hover:underline"
                >Go to Login</a
            >
        </div>
    {/if}
</div>

<style>
    .input {
        @apply px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 transition-colors;
    }
</style>
