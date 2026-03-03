"use client";

import Link from "next/link";
import styles from "./GridNav.module.css";

const NAV_LINKS = [
  { href: "/", label: "Sanctum" },
  { href: "/flame", label: "Flame" },
  { href: "/flame-map", label: "Flame Map" },
  { href: "/hyperspine", label: "Hyper-Spine" },
  { href: "/chat", label: "Oracle Chat" },
  { href: "/backend", label: "Backend" },
  { href: "/grid-vitals", label: "Grid Vitals" },
];

export default function GridNav() {
  return (
    <div className={styles.navRow}>
      {NAV_LINKS.map((link) => (
        <Link key={link.href} href={link.href} className={styles.navButton}>
          {link.label}
        </Link>
      ))}
    </div>
  );
}

