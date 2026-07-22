import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

/**
 * Routes that require authentication.
 * Unauthenticated users are redirected to /login with a returnUrl param.
 */
const PROTECTED_ROUTES = ["/profile", "/works", "/keys", "/topup"]

/**
 * Routes that should redirect authenticated users away (e.g., login page).
 */
const AUTH_ROUTES = ["/login"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Read auth state from localStorage via a cookie approach.
  // Next.js middleware runs on the edge and cannot access localStorage.
  // We use a lightweight cookie set by the client to track auth state.
  const authCookie = request.cookies.get("agnes-auth")

  const isAuthenticated = authCookie?.value === "1"

  // Redirect unauthenticated users trying to access protected routes
  if (PROTECTED_ROUTES.some((route) => pathname.startsWith(route))) {
    if (!isAuthenticated) {
      const loginUrl = new URL("/login", request.url)
      loginUrl.searchParams.set("redirect", pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  // Redirect authenticated users away from login page
  if (AUTH_ROUTES.some((route) => pathname === route)) {
    if (isAuthenticated) {
      const redirectUrl = request.nextUrl.searchParams.get("redirect") || "/"
      return NextResponse.redirect(new URL(redirectUrl, request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  // Match all paths except static files, API routes, and Next.js internals
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)"],
}
