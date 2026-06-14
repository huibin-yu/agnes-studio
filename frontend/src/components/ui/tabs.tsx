"use client"

import { cn } from "@/lib/utils"
import * as TabsPrimitiveUI from "@radix-ui/react-tabs"
import * as React from "react"

const Tabs = TabsPrimitiveUI.Root

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitiveUI.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitiveUI.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitiveUI.List
    ref={ref}
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground",
      className
    )}
    {...props}
  />
))
TabsList.displayName = TabsPrimitiveUI.List.displayName

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitiveUI.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitiveUI.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitiveUI.Trigger
    ref={ref}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow",
      className
    )}
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitiveUI.Trigger.displayName

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitiveUI.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitiveUI.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitiveUI.Content
    ref={ref}
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
      className
    )}
    {...props}
  />
))
TabsContent.displayName = TabsPrimitiveUI.Content.displayName

export { Tabs, TabsList, TabsTrigger, TabsContent }
