"use client";

import { useEffect, useState } from "react";
import confetti from "canvas-confetti";

interface SuccessConfettiProps {
  trigger: boolean;
  message?: string;
}

export function SuccessConfetti({ trigger, message }: SuccessConfettiProps) {
  const [showMessage, setShowMessage] = useState(false);

  useEffect(() => {
    if (trigger) {
      // Fire confetti
      const duration = 3 * 1000;
      const animationEnd = Date.now() + duration;
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

      const randomInRange = (min: number, max: number) => {
        return Math.random() * (max - min) + min;
      };

      const interval: any = setInterval(() => {
        const timeLeft = animationEnd - Date.now();

        if (timeLeft <= 0) {
          return clearInterval(interval);
        }

        const particleCount = 50 * (timeLeft / duration);

        // Fire from two sides
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
        });
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
        });
      }, 250);

      // Show success message
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 4000);

      return () => clearInterval(interval);
    }
  }, [trigger]);

  if (!showMessage) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-50">
      <div className="animate-bounce bg-gradient-to-r from-green-500 to-blue-500 text-white px-8 py-4 rounded-full shadow-2xl text-xl font-bold">
        {message || "🎉 Success! Impact Card Generated!"}
      </div>
    </div>
  );
}

// Installation: npm install canvas-confetti
// Usage: <SuccessConfetti trigger={impactCardGenerated} message="🎉 Impact Card Complete!" />