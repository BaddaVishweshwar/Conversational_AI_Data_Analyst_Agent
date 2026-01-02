import { useState } from 'react';

export function useToast() {
    const toast = ({ title, description, variant }: { title: string, description?: string, variant?: string }) => {
        console.log(`Toast: ${title} - ${description} (${variant})`);
        alert(`${title}\n${description || ''}`);
    };

    return { toast };
}
