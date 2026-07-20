"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Image, Video, Sparkles, Zap, Users, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"

const features = [
  {
    icon: Image,
    title: "AI 文生图",
    description: "支持 14+ 种艺术风格，一键生成高质量图片。从照片级写实到动漫风格，满足各种创意需求。",
    gradient: "from-violet-500 to-purple-600",
  },
  {
    icon: Video,
    title: "AI 文生视频",
    description: "输入文字描述，生成电影质感短视频。支持多种风格和分辨率，让创意动了起来。",
    gradient: "from-pink-500 to-rose-600",
  },
  {
    icon: Sparkles,
    title: "智能提示词增强",
    description: "自动优化你的提示词，添加专业关键词和风格描述，让生成效果更好。",
    gradient: "from-amber-500 to-orange-600",
  },
  {
    icon: Users,
    title: "社区画廊",
    description: "浏览社区精选作品，获取灵感，点赞收藏你喜欢的作品，与其他创作者交流。",
    gradient: "from-emerald-500 to-teal-600",
  },
]

const styles = [
  "摄影写实", "电影质感", "动漫风格", "数字艺术",
  "油画风格", "水彩画", "3D 渲染", "像素艺术",
  "科幻", "奇幻", "波普艺术", "极简主义",
]

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-32 pb-20 px-4">
        {/* Background effects */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl" />
        </div>

        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
              <Zap className="w-4 h-4" />
              Agnes AI 驱动 · 注册送积分
            </div>

            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              用 AI 释放你的
              <br />
              <span className="gradient-text">创意潜能</span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
              输入文字描述，AI 帮你生成精美的图片和视频。
              <br />
              支持 14+ 种艺术风格，从写实摄影到梦幻动漫。
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/generate/image">
                <Button size="lg" className="gap-2 px-8 text-base">
                  <Sparkles className="w-5 h-5" />
                  开始生图
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/generate/video">
                <Button size="lg" variant="outline" className="gap-2 px-8 text-base">
                  <Video className="w-5 h-5" />
                  生成视频
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Style showcase */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="mt-16 flex flex-wrap justify-center gap-2"
          >
            {styles.map((style, i) => (
              <span
                key={i}
                className="px-3 py-1.5 rounded-full bg-muted text-sm text-muted-foreground"
              >
                {style}
              </span>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">强大功能，简单易用</h2>
            <p className="text-muted-foreground text-lg">
              从创意到成品，只需几步操作
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="group p-6 rounded-xl border border-border bg-card hover:border-primary/30 transition-all"
              >
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center p-12 rounded-2xl bg-gradient-to-br from-violet-500/10 via-purple-500/10 to-pink-500/10 border border-primary/20">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">准备好开始创作了吗？</h2>
          <p className="text-muted-foreground text-lg mb-8">
            注册即送 12 免费积分，体验 AI 生成的魅力
          </p>
          <Link href="/register">
            <Button size="lg" variant="glow" className="gap-2 px-8 text-base">
              免费开始
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t text-center text-sm text-muted-foreground">
        <p>© 2026 Agnes Studio. Powered by Agnes AI</p>
      </footer>
    </div>
  )
}
