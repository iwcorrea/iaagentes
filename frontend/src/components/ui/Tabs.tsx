"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  badge?: number | string;
  disabled?: boolean;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  variant?: "underline" | "pills" | "buttons";
  className?: string;
  children?: React.ReactNode;
}

export const Tabs = ({
  tabs,
  defaultTab,
  onChange,
  variant = "underline",
  className,
  children,
}: TabsProps) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  const variantStyles = {
    underline: {
      container: "border-b border-cream-200",
      tab: (isActive: boolean, disabled?: boolean) =>
        cn(
          "relative px-4 py-3 text-sm font-medium transition-colors",
          disabled && "opacity-40 cursor-not-allowed",
          isActive
            ? "text-brand-600"
            : "text-earth-500 hover:text-earth-700"
        ),
      indicator: "absolute bottom-0 left-0 right-0 h-0.5 bg-brand-600",
    },
    pills: {
      container: "flex flex-wrap gap-2",
      tab: (isActive: boolean, disabled?: boolean) =>
        cn(
          "px-4 py-2 rounded-xl text-sm font-medium transition-all",
          disabled && "opacity-40 cursor-not-allowed",
          isActive
            ? "bg-brand-600 text-white shadow-sm"
            : "bg-cream-100 text-earth-600 hover:bg-cream-200"
        ),
      indicator: null,
    },
    buttons: {
      container: "flex gap-1 p-1 bg-cream-100 rounded-2xl",
      tab: (isActive: boolean, disabled?: boolean) =>
        cn(
          "px-4 py-2 rounded-xl text-sm font-medium transition-all",
          disabled && "opacity-40 cursor-not-allowed",
          isActive
            ? "bg-white text-earth-900 shadow-sm"
            : "text-earth-500 hover:text-earth-700"
        ),
      indicator: null,
    },
  };

  const styles = variantStyles[variant];

  return (
    <div className={className}>
      <div className={styles.container}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && handleTabClick(tab.id)}
            disabled={tab.disabled}
            className={cn(
              styles.tab(tab.id === activeTab, tab.disabled),
              "relative"
            )}
          >
            <div className="flex items-center gap-2">
              {tab.icon}
              {tab.label}
              {tab.badge !== undefined && (
                <span className="inline-flex items-center justify-center h-5 min-w-5 px-1.5 rounded-full bg-brand-100 text-brand-700 text-2xs font-bold">
                  {tab.badge}
                </span>
              )}
            </div>
            {styles.indicator && tab.id === activeTab && (
              <motion.div
                layoutId="tab-indicator"
                className={styles.indicator}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        ))}
      </div>
      {children && (
        <div className="mt-6">
          {React.Children.map(children, (child) => {
            if (React.isValidElement(child) && child.props.tabId === activeTab) {
              return child;
            }
            return null;
          })}
        </div>
      )}
    </div>
  );
};

export const TabPanel = ({
  tabId,
  children,
}: {
  tabId: string;
  children: React.ReactNode;
}) => {
  return <div>{children}</div>;
};
