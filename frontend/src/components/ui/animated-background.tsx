"use client";

import { motion } from "framer-motion";
import clsx from "clsx";

interface AnimatedBackgroundProps {
    className?: string;
    variant?: "accent" | "emerald" | "teal";
}

const COLOR_VARIANTS = {
    accent: {
        border: [
            "border-accent/60",
            "border-emerald-400/50",
            "border-teal-600/30",
        ],
        gradient: "from-accent/40",
        glow: "bg-[radial-gradient(ellipse_at_center,#00bfa5/20%,transparent_70%)]",
    },
    emerald: {
        border: [
            "border-emerald-500/60",
            "border-teal-400/50",
            "border-accent/30",
        ],
        gradient: "from-emerald-500/40",
        glow: "bg-[radial-gradient(ellipse_at_center,#10b981/20%,transparent_70%)]",
    },
    teal: {
        border: [
            "border-teal-500/60",
            "border-cyan-400/50",
            "border-accent/30",
        ],
        gradient: "from-teal-500/40",
        glow: "bg-[radial-gradient(ellipse_at_center,#14b8a6/20%,transparent_70%)]",
    },
} as const;

const AnimatedGrid = () => (
    <motion.div
        className="absolute inset-0 [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]"
        animate={{
            backgroundPosition: ["0% 0%", "100% 100%"],
        }}
        transition={{
            duration: 60,
            repeat: Infinity,
            ease: "linear",
        }}
    >
        <div className="h-full w-full [background-image:repeating-linear-gradient(100deg,#00bfa5_0%,#00bfa5_1px,transparent_1px,transparent_4%)] opacity-10" />
    </motion.div>
);

export function AnimatedBackground({
    className,
    variant = "accent",
}: AnimatedBackgroundProps) {
    const variantStyles = COLOR_VARIANTS[variant];

    return (
        <div
            className={clsx(
                "absolute inset-0 overflow-hidden",
                className
            )}
        >
            <AnimatedGrid />

            {/* Animated Rotating Circles */}
            <motion.div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px]">
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        className={clsx(
                            "absolute inset-0 rounded-full",
                            "border-2 bg-gradient-to-br to-transparent",
                            variantStyles.border[i],
                            variantStyles.gradient
                        )}
                        animate={{
                            rotate: i % 2 === 0 ? 360 : -360,
                            scale: [1, 1.08 + i * 0.04, 1],
                            opacity: [0.6, 1, 0.6],
                        }}
                        transition={{
                            duration: 20 + i * 5,
                            repeat: Infinity,
                            ease: "easeInOut",
                        }}
                        style={{
                            transformOrigin: "center",
                        }}
                    >
                        <div
                            className={clsx(
                                "absolute inset-0 rounded-full mix-blend-screen blur-sm",
                                variantStyles.glow
                            )}
                        />
                    </motion.div>
                ))}
            </motion.div>

            {/* Radial Gradient Glows */}
            <div className="absolute inset-0 [mask-image:radial-gradient(80%_60%_at_50%_50%,#000_30%,transparent)]">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,#00bfa5/25%,transparent_70%)] blur-[100px]" />
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,#10b981/15%,transparent)] blur-[60px]" />
            </div>
        </div>
    );
}
