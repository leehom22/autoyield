import { create } from 'zustand';

export interface Toast {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

interface ToastState {
  toasts: Toast[];
  errors: { timestamp: string; message: string }[];
  addToast: (type: Toast['type'], message: string) => void;
  removeToast: (id: string) => void;
  addError: (message: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  errors: [],
  addToast: (type, message) => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      toasts: [...state.toasts, { id, type, message }]
    }));
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id)
      }));
    }, 5000);
  },
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter((t) => t.id !== id)
  })),
  addError: (message) => set((state) => ({
    errors: [{ timestamp: new Date().toISOString(), message }, ...state.errors].slice(0, 50)
  }))
}));
