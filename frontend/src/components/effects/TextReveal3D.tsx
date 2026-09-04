'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface TextReveal3DProps {
  lines: string[];
  className?: string;
  delay?: number;
}

const WORD_VARIANTS = {
  hidden: {
    opacity: 0,
    rotateX: -90,
    y: 24,
    filter: 'blur(4px)',
  },
  visible: (i: number) => ({
    opacity: 1,
    rotateX: 0,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.65,
      delay: i * 0.055,
      ease: [0.215, 0.61, 0.355, 1.0],
    },
  }),
};

export default function TextReveal3D({ lines, className = '', delay = 0 }: TextReveal3DProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-80px 0px' });

  let wordIndex = 0;
  const allWords = lines.map(line => line.split(' ').filter(Boolean));

  return (
    <div
      ref={ref}
      className={`text-reveal-3d ${className}`}
      style={{ perspective: '800px' }}
    >
      {allWords.map((words, lineIdx) => (
        <div key={lineIdx} className="overflow-hidden leading-[1.1]" style={{ display: 'block' }}>
          {words.map((word) => {
            const currentIndex = wordIndex++;
            return (
              <span
                key={currentIndex}
                style={{ display: 'inline-block', marginRight: '0.25em', transformOrigin: '50% 100%' }}
              >
                <motion.span
                  custom={currentIndex + delay * 18}
                  variants={WORD_VARIANTS}
                  initial="hidden"
                  animate={inView ? 'visible' : 'hidden'}
                  style={{ display: 'inline-block', transformOrigin: '50% 100%' }}
                >
                  {word}
                </motion.span>
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
}
