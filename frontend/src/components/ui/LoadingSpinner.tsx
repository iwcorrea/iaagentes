"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  variant?: "brand" | "white" | "earth";
  className?: string;
  text?: string;
}

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
  xl: "h-12 w-12",
};

const variantMap = {
  brand: "text-brand-600",
  white: "text-white",
  earth: "text-earth-600",
};

export const LoadingSpinner = ({
  size = "md",
  variant = "brand",
  className,
  text,
}: LoadingSpinnerProps) => {
  return (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2
        className={cn(
          "animate-spin",
          sizeMap[size],
          variantMap[variant],
          className
        )}
      />
      {text && (
        <p className="text-sm text-earth-500 animate-pulse">{text}</p>
      )}
    </div>
  );
};

export const PageLoader = () => {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <LoadingSpinner size="xl" text="Cargando..." />
    </div>
  );
};

export const SkeletonCard = () => {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-soft animate-pulse">
      <div className="aspect-square bg-cream-200" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-cream-200 rounded w-3/4" />
        <div className="h-3 bg-cream-200 rounded w-1/2" />
        <div className="h-6 bg-cream-200 rounded w-1/3" />
        <div className="h-10 bg-cream-200 rounded-xl" />
      </div>
    </div>
  );
};
