"use client";

import React from "react";
import { Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuantitySelectorProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  size?: "sm" | "md";
  disabled?: boolean;
}

export const QuantitySelector = ({
  value,
  onChange,
  min = 1,
  max = 99,
  size = "md",
  disabled = false,
}: QuantitySelectorProps) => {
  const isMin = value <= min;
  const isMax = value >= max;

  const sizeStyles = {
    sm: {
      button: "h-8 w-8",
      input: "h-8 w-12 text-sm",
      icon: "h-3.5 w-3.5",
    },
    md: {
      button: "h-10 w-10",
      input: "h-10 w-16 text-base",
      icon: "h-4 w-4",
    },
  };

  const styles = sizeStyles[size];

  return (
    <div className="flex items-center gap-0">
      <button
        type="button"
        disabled={isMin || disabled}
        onClick={() => onChange(value - 1)}
        className={cn(
          styles.button,
          "flex items-center justify-center rounded-l-xl border-2 border-r-0 border-cream-300 bg-white text-earth-600 transition-all",
          "hover:bg-earth-50 hover:text-brand-600",
          "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:text-earth-600"
        )}
        aria-label="Disminuir cantidad"
      >
        <Minus className={styles.icon} />
      </button>
      <input
        type="number"
        value={value}
        onChange={(e) => {
          const val = parseInt(e.target.value) || min;
          onChange(Math.min(max, Math.max(min, val)));
        }}
        disabled={disabled}
        className={cn(
          styles.input,
          "text-center font-medium text-earth-900 border-2 border-x-0 border-cream-300 bg-white outline-none",
          "[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
        )}
        min={min}
        max={max}
      />
      <button
        type="button"
        disabled={isMax || disabled}
        onClick={() => onChange(value + 1)}
        className={cn(
          styles.button,
          "flex items-center justify-center rounded-r-xl border-2 border-l-0 border-cream-300 bg-white text-earth-600 transition-all",
          "hover:bg-earth-50 hover:text-brand-600",
          "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white disabled:hover:text-earth-600"
        )}
        aria-label="Aumentar cantidad"
      >
        <Plus className={styles.icon} />
      </button>
    </div>
  );
};
