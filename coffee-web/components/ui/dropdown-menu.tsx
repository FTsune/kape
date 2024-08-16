// src/components/ui/dropdown-menu.tsx

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import React from "react";
import { cn } from "@/lib/utils"; // Ensure this path is correct

const DropdownMenu: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DropdownMenuPrimitive.Root>
    {children}
  </DropdownMenuPrimitive.Root>
);

const DropdownMenuTrigger: React.FC<{ asChild?: boolean; children: React.ReactNode }> = ({ asChild, children }) => (
  <DropdownMenuPrimitive.Trigger asChild={asChild}>
    {children}
  </DropdownMenuPrimitive.Trigger>
);

const DropdownMenuContent: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <DropdownMenuPrimitive.Content className={cn("dropdown-menu-content", className)}>
    {children}
  </DropdownMenuPrimitive.Content>
);

const DropdownMenuLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <DropdownMenuPrimitive.Label>
    {children}
  </DropdownMenuPrimitive.Label>
);

const DropdownMenuSeparator: React.FC = () => (
  <DropdownMenuPrimitive.Separator />
);

const DropdownMenuCheckboxItem: React.FC<React.ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>> = (props) => (
  <DropdownMenuPrimitive.CheckboxItem {...props} />
);

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
};
