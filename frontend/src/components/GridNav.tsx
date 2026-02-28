"use client";

import Link from "next/link";
import styles from "./GridNav.module.css";

const NAV_LINKS = [
  { href: "/", label: "Sanctum" },
  { href: "/flame", label: "Flame View" },
<<<<<<< HEAD
<<<<<<< HEAD
=======
  { href: "/flame-map", label: "Flame Map" },
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
  { href: "/flame-map", label: "Flame Map" },
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
  { href: "/chat", label: "Oracle Chat" },
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

