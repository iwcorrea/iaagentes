import { useState } from 'react';
import api from '../api/axios';
export function useImprovements() {
  const applyImprovement = async (id) => {
    try {
      await api.patch(`/improvements/${id}`, { status: 'applied' });
    } catch (e) {
      console.error(e);
    }
  };
  return { applyImprovement };
}