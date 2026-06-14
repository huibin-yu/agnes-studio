"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Image, Video, Images, User, Home, Menu, X, FolderOpen } from "lucide-react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/stores/auth"

const navItems = [
  { href: "/", label: "首页", icon: Home },
  { href: "/generate/image", label: "生图", icon: Image },
  { href: "/generate/video", label: "生视频", icon: Video },
  { href: "/gallery", label: "画廊", icon: Images },
  { href: "/works", label: "作品", icon: FolderOpen },
  { href: "/profile", label: "我的", icon: User },
]

export default function Navbar() {
  const pathname = usePathname()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, isAuthenticated, logout } = useAuthStore()

  return (
    <>
      {/* Skip to content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-lg"
      >
        跳过导航
      </a>
      <nav className="fixed top-0 left-0 right-0 z-40 border-b bg-background/80 backdrop-blur-xl" role="navigation" aria-label="主导航">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2" aria-label="Agnes Studio 首页">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <span className="font-bold text-lg">Agnes Studio</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href ||
                  (item.href !== "/" && pathname?.startsWith(item.href))
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    )}
                  >
                    <item.icon className="w-4 h-4 inline mr-1.5" aria-hidden="true" />
                    {item.label}
                  </Link>
                )
              })}
            </div>

            {/* User section */}
            <div className="hidden md:flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/50">
                    <span className="text-xs text-muted-foreground">积分</span>
                    <span className="text-sm font-semibold text-primary">{user?.credits ?? 0}</span>
                  </div>
                  <Link
                    href="/profile"
                    className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold"
                    aria-label={`个人中心: ${user?.username}`}
                  >
                    {user?.username?.[0]?.toUpperCase() ?? "U"}
                  </Link>
                </>
              ) : (
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity"
                >
                  登录
                </Link>
              )}
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 rounded-lg hover:bg-muted"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-expanded={mobileOpen}
              aria-label={mobileOpen ? "关闭菜单" : "打开菜单"}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t bg-background">
            <div className="px-4 py-3 space-y-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted"
                    )}
                  >
                    <item.icon className="w-4 h-4" aria-hidden="true" />
                    {item.label}
                  </Link>
                )
              })}
              <div className="pt-2 border-t mt-2">
                {isAuthenticated ? (
                  <>
                    <div className="px-3 py-2 text-sm">
                      积分: <span className="font-semibold text-primary">{user?.credits}</span>
                    </div>
                    <button
                      onClick={() => { logout(); setMobileOpen(false) }}
                      className="w-full text-left px-3 py-2 text-sm text-destructive hover:bg-muted rounded-lg"
                    >
                      退出登录
                    </button>
                  </>
                ) : (
                  <Link
                    href="/login"
                    onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg text-center"
                  >
                    登录
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}
      </nav>
    </>
  )
}
