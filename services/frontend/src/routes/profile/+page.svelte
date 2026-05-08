<script lang="ts">
    import { onMount } from "svelte";
    import { fade, slide } from "svelte/transition";
    import { getProfile, updateProfile, uploadProfilePicture, deleteProfilePicture, getUserCVs, uploadUserCV, updateUserCV, activateUserCV, deleteUserCV } from "$lib/api";
    import type { UserCVRead } from "$lib/api";
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
    let message = "";
    let error = "";

    // Profile Picture logic
    let isPictureModalOpen = false;
    let fileInput: HTMLInputElement;
    let imageToCrop: string | null = null;
    let cropperRef: HTMLImageElement;
    let cropperInstance: Cropper | null = null;
    let isUploading = false;
    let isDeleting = false;

    // CV Management
    let cvList: UserCVRead[] = [];
    let isCvLoading = false;
    let isCvUploading = false;
    let cvFileInput: HTMLInputElement;
    let showCvUploadForm = false;
    let newCvName = "My CV";
    let editingCvId: number | null = null;
    let editingCvName = "";

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

    function closePictureModal() {
        if (cropperInstance) {
            cropperInstance.destroy();
            cropperInstance = null;
        }
        imageToCrop = null;
        isPictureModalOpen = false;
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
                    const updatedUser = await uploadProfilePicture(blob);
                    user = updatedUser;
                    auth.updateUser(user);
                    message = "Profile picture updated successfully!";
                    closePictureModal();
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
            const updatedUser = await deleteProfilePicture();
            user = updatedUser;
            auth.updateUser(user);
            message = "Profile picture deleted successfully!";
            closePictureModal();
        } catch (err: any) {
            error = err.message || "Failed to delete image";
        } finally {
            isDeleting = false;
        }
    }

    // ── CV Management Functions ─────────────────────────────────────────────

    async function loadCVs() {
        isCvLoading = true;
        try {
            cvList = await getUserCVs();
        } catch (e: any) {
            console.error("Failed to load CVs:", e);
        } finally {
            isCvLoading = false;
        }
    }

    function handleCvFileSelect(event: Event) {
        const file = (event.target as HTMLInputElement).files?.[0];
        if (!file) return;
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            error = "Please select a PDF file";
            cvFileInput.value = '';
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            error = "File size must be less than 10MB";
            cvFileInput.value = '';
            return;
        }
        showCvUploadForm = true;
    }

    async function handleCvUpload() {
        const file = cvFileInput?.files?.[0];
        if (!file) return;

        isCvUploading = true;
        error = "";
        message = "";
        try {
            const uploaded = await uploadUserCV(file, newCvName || "My CV");
            cvList = [...cvList, uploaded];
            // Sort: active first, then by date desc
            cvList.sort((a, b) => {
                if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });
            message = `CV "${uploaded.name}" uploaded successfully!`;
            showCvUploadForm = false;
            newCvName = "My CV";
            if (cvFileInput) cvFileInput.value = '';
        } catch (e: any) {
            error = e.message || "Failed to upload CV";
        } finally {
            isCvUploading = false;
        }
    }

    function cancelCvUpload() {
        showCvUploadForm = false;
        newCvName = "My CV";
        if (cvFileInput) cvFileInput.value = '';
    }

    async function handleActivateCv(cvId: number) {
        error = "";
        message = "";
        try {
            await activateUserCV(cvId);
            cvList = cvList.map(cv => ({ ...cv, is_active: cv.id === cvId }));
            // Re-sort
            cvList.sort((a, b) => {
                if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
                return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            });
            message = "Active CV updated!";
        } catch (e: any) {
            error = e.message || "Failed to activate CV";
        }
    }

    function startRenameCv(cv: UserCVRead) {
        editingCvId = cv.id;
        editingCvName = cv.name;
    }

    async function handleRenameCv(cvId: number) {
        if (!editingCvName.trim()) return;
        error = "";
        try {
            const updated = await updateUserCV(cvId, { name: editingCvName.trim() });
            cvList = cvList.map(cv => cv.id === cvId ? { ...cv, name: updated.name } : cv);
            editingCvId = null;
            editingCvName = "";
        } catch (e: any) {
            error = e.message || "Failed to rename CV";
        }
    }

    function cancelRenameCv() {
        editingCvId = null;
        editingCvName = "";
    }

    async function handleDeleteCv(cv: UserCVRead) {
        if (!confirm(`Delete "${cv.name}"? This cannot be undone.`)) return;
        error = "";
        message = "";
        try {
            await deleteUserCV(cv.id);
            cvList = cvList.filter(c => c.id !== cv.id);
            // If the deleted CV was active and there are remaining CVs, reload to get new active
            if (cv.is_active && cvList.length > 0) {
                await loadCVs();
            }
            message = `CV "${cv.name}" deleted.`;
        } catch (e: any) {
            error = e.message || "Failed to delete CV";
        }
    }

    function formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }

    onMount(async () => {
        try {
            user = await getProfile();
            auth.updateUser(user!);
            await loadCVs();
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
    <div class="flex justify-between items-start mb-6 pb-6 border-b border-gray-100">
        <h1 class="text-2xl font-bold text-gray-800 mt-2">My Profile</h1>
        
        {#if !isLoading && user}
            <button 
                type="button"
                on:click={() => isPictureModalOpen = true}
                class="relative group rounded-full w-20 h-20 sm:w-24 sm:h-24 block overflow-hidden focus:outline-none focus:ring-4 focus:ring-primary-100 shadow-md -mt-2"
            >
                {#if user.profile_picture_url}
                    <img src={user.profile_picture_url} alt="Profile" class="w-full h-full object-cover border-4 border-white bg-gray-50 transition-opacity duration-200 group-hover:opacity-75" />
                {:else}
                    <div class="w-full h-full rounded-full bg-primary-50 text-primary-600 flex items-center justify-center text-3xl font-bold border-4 border-white transition-opacity duration-200 group-hover:opacity-75">
                        {user.first_name?.[0] || user.email[0].toUpperCase()}
                    </div>
                {/if}
                <!-- Hover Overlay -->
                <div class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 sm:h-8 sm:w-8 text-white drop-shadow-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                </div>
            </button>
        {/if}
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



        {#if isPictureModalOpen}
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" transition:fade={{ duration: 150 }}>
            <div class="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
                <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-white z-10">
                    <h3 class="font-bold text-gray-800">{imageToCrop ? 'Crop profile picture' : 'Profile picture'}</h3>
                    <button on:click={closePictureModal} class="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-full hover:bg-gray-100">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                {#if imageToCrop}
                    <!-- Cropper State -->
                    <div class="p-6 bg-gray-50 flex-1 overflow-auto flex items-center justify-center">
                        <div class="w-full aspect-square relative bg-white shadow-inner max-w-[300px] mx-auto overflow-hidden">
                            <img bind:this={cropperRef} src={imageToCrop} alt="To crop" class="block max-w-full" />
                        </div>
                    </div>
                    
                    <div class="p-4 border-t border-gray-100 flex justify-end gap-3 bg-white">
                        <button on:click={cancelCrop} class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors">
                            Back
                        </button>
                        <button on:click={handleCropSave} disabled={isUploading} class="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2">
                            {#if isUploading}
                                <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Saving...
                            {:else}
                                Save
                            {/if}
                        </button>
                    </div>
                {:else}
                    <!-- Display State -->
                    <div class="p-8 bg-gray-50 flex-1 flex flex-col items-center justify-center">
                        <div class="w-48 h-48 sm:w-64 sm:h-64 rounded-full overflow-hidden border-[12px] border-white shadow-xl bg-white mb-4 relative group">
                            {#if user.profile_picture_url}
                                <img src={user.profile_picture_url} alt="Profile" class="w-full h-full object-cover" />
                            {:else}
                                <div class="w-full h-full bg-primary-50 text-primary-600 flex items-center justify-center text-7xl font-bold">
                                    {user.first_name?.[0] || user.email[0].toUpperCase()}
                                </div>
                            {/if}
                        </div>
                    </div>
                    
                    <div class="p-4 border-t border-gray-100 bg-white">
                        <div class="flex flex-col sm:flex-row gap-3 justify-center">
                            <input type="file" accept="image/*" class="hidden" bind:this={fileInput} on:change={handleFileSelect} />
                            <button type="button" on:click={() => fileInput.click()} class="px-6 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors shadow-sm flex-1 flex items-center justify-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                </svg>
                                Upload Photo
                            </button>
                            {#if user.profile_picture_url}
                                <button type="button" on:click={handleDeletePicture} disabled={isDeleting} class="px-6 py-2 text-red-600 border border-slate-200 bg-white rounded-lg text-sm font-medium hover:bg-red-50 hover:border-red-100 transition-colors disabled:opacity-50 flex-1 flex items-center justify-center gap-2 shadow-sm">
                                    {#if isDeleting}
                                        Deleting...
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                        Delete
                                    {/if}
                                </button>
                            {/if}
                        </div>
                    </div>
                {/if}
            </div>
        </div>
        {/if}

        <!-- My CVs Section -->
        <div class="mb-8 pb-8 border-b border-gray-100">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    My CVs
                    <span class="text-xs font-normal text-gray-400">({cvList.length}/5)</span>
                </h3>
                {#if cvList.length < 5}
                    <div>
                        <input type="file" accept=".pdf" class="hidden" bind:this={cvFileInput} on:change={handleCvFileSelect} />
                        <button
                            type="button"
                            on:click={() => cvFileInput.click()}
                            disabled={isCvUploading}
                            class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                            </svg>
                            Upload CV
                        </button>
                    </div>
                {/if}
            </div>

            <!-- Upload Form (shown after file selected) -->
            {#if showCvUploadForm}
                <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                    <p class="text-sm text-gray-600 mb-2">
                        File: <span class="font-medium text-gray-800">{cvFileInput?.files?.[0]?.name || ''}</span>
                    </p>
                    <label for="cv-name" class="block text-sm font-medium text-gray-700 mb-1">Give this CV a name</label>
                    <div class="flex gap-2">
                        <input
                            id="cv-name"
                            type="text"
                            bind:value={newCvName}
                            placeholder="e.g. Tech Lead CV"
                            class="input flex-1"
                        />
                        <button
                            type="button"
                            on:click={handleCvUpload}
                            disabled={isCvUploading}
                            class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                        >
                            {#if isCvUploading}
                                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Uploading...
                            {:else}
                                Save
                            {/if}
                        </button>
                        <button type="button" on:click={cancelCvUpload} class="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium transition-colors">
                            Cancel
                        </button>
                    </div>
                </div>
            {/if}

            <!-- CV List -->
            {#if isCvLoading}
                <div class="text-center py-6 text-gray-400 text-sm">Loading CVs...</div>
            {:else if cvList.length === 0}
                <div class="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p class="text-gray-500 text-sm mb-1">No CVs uploaded yet</p>
                    <p class="text-gray-400 text-xs">Upload your CV to auto-fill cover letters</p>
                </div>
            {:else}
                <div class="space-y-3">
                    {#each cvList as cv (cv.id)}
                        <div transition:slide={{ duration: 250 }} class="group flex items-center gap-4 p-4 rounded-xl border {cv.is_active ? 'border-primary-400 bg-primary-50/30 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300'} transition-all duration-200">
                            <!-- Icon -->
                            <div class="shrink-0 {cv.is_active ? 'text-primary-600 bg-primary-100/50' : 'text-slate-400 bg-slate-50'} p-2.5 rounded-lg border border-slate-100">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>

                            <!-- Info -->
                            <div class="flex-1 min-w-0">
                                {#if editingCvId === cv.id}
                                    <div class="flex gap-2" transition:fade={{ duration: 150 }}>
                                        <input
                                            type="text"
                                            bind:value={editingCvName}
                                            on:keydown={(e) => { if (e.key === 'Enter') handleRenameCv(cv.id); if (e.key === 'Escape') cancelRenameCv(); }}
                                            class="input text-sm flex-1 py-1 px-2 min-w-0"
                                            autofocus
                                        />
                                        <button on:click={() => handleRenameCv(cv.id)} class="px-3 py-1 text-primary-600 hover:text-primary-700 text-xs font-semibold rounded-md border border-primary-200 hover:bg-primary-50 transition-colors">Save</button>
                                        <button on:click={cancelRenameCv} class="px-3 py-1 text-slate-500 hover:text-slate-700 text-xs font-medium rounded-md border border-slate-200 hover:bg-slate-50 transition-colors">Cancel</button>
                                    </div>
                                {:else}
                                    <div class="flex items-center gap-2" transition:fade={{ duration: 150 }}>
                                        <span class="font-semibold text-sm text-slate-800 truncate">{cv.name}</span>
                                        {#if cv.is_active}
                                            <span class="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wide bg-primary-100 text-primary-700 border border-primary-200">Active</span>
                                        {/if}
                                    </div>
                                    <p class="text-xs text-slate-400 truncate mt-0.5">{cv.original_filename} · {formatDate(cv.created_at)}</p>
                                {/if}
                            </div>

                            <!-- Actions -->
                            <div class="shrink-0 flex items-center gap-1 opacity-100 sm:opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity duration-200">
                                {#if !cv.is_active}
                                    <button
                                        type="button"
                                        on:click={() => handleActivateCv(cv.id)}
                                        title="Set as active"
                                        class="p-2 text-slate-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors border border-transparent hover:border-primary-100"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                                        </svg>
                                    </button>
                                {/if}
                                <a
                                    href={cv.cv_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    title="View PDF"
                                    class="p-2 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-slate-200"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                </a>
                                <button
                                    type="button"
                                    on:click={() => startRenameCv(cv)}
                                    title="Rename"
                                    class="p-2 text-slate-400 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors border border-transparent hover:border-slate-200"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                    </svg>
                                </button>
                                <button
                                    type="button"
                                    on:click={() => handleDeleteCv(cv)}
                                    title="Delete"
                                    class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors border border-transparent hover:border-red-100"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>

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

                <div class="md:col-span-2 pt-6 mt-2">
                    <div class="bg-slate-50/50 border border-slate-200 rounded-xl p-6 shadow-sm">
                        <div class="flex items-center gap-3 mb-5 border-b border-slate-100 pb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            <h3 class="text-lg font-semibold text-slate-800">Address</h3>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                            <div class="md:col-span-2">
                                <label
                                    for="street"
                                    class="block text-sm font-medium text-slate-700 mb-1"
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
                                    class="block text-sm font-medium text-slate-700 mb-1"
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
                                    class="block text-sm font-medium text-slate-700 mb-1"
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
                                    class="block text-sm font-medium text-slate-700 mb-1"
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
                    </div>
                </div>
            </div>

            <div class="pt-6 border-t border-gray-100 flex flex-col items-end gap-3">
                <button
                    type="submit"
                    disabled={isSaving}
                    class="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                    {isSaving ? "Saving..." : "Save Changes"}
                </button>
                <div class="flex items-start sm:items-center gap-2 text-xs text-slate-400 max-w-sm text-right">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mt-0.5 sm:mt-0 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p>The contact information will be used for the header of the covering letter, and will be used only for this purpose.</p>
                </div>
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
        @apply px-3 py-2 border border-slate-200 rounded-lg shadow-sm focus:ring-primary-500 focus:border-primary-500 transition-colors bg-white;
    }
</style>
