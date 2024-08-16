// src/components/ui/button.tsx

"use client";

import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline";
  size?: "small" | "medium" | "large";
};

export const Button: React.FC<ButtonProps> = ({
  variant = "default",
  size = "medium",
  className,
  ...props
}) => {
  const baseStyle = "px-4 py-2 rounded focus:outline-none";
  const variantStyle =
    variant === "outline" ? "border border-gray-500" : "bg-blue-500 text-white";
  const sizeStyle =
    size === "small" ? "text-sm" :
    size === "large" ? "text-lg" : "text-base";

  return (
    <button className={`${baseStyle} ${variantStyle} ${sizeStyle} ${className}`} {...props}>
      {props.children}
    </button>
  );
};
