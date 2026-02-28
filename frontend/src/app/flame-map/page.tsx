<<<<<<< HEAD
<<<<<<< HEAD
import { redirect } from "next/navigation";

export default function FlameMapPage() {
  // Consolidated: redirect Flame Map to the main Flame view
  redirect("/flame");
=======
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
import AfricanFlameMap from "@/components/AfricanFlameMap";

export default function FlameMapPage() {
  return (
    <main>
      <AfricanFlameMap />
    </main>
  );
<<<<<<< HEAD
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
=======
>>>>>>> cfb3fc4e0dd0b8cbddb51f7c6fd9c0230cce6d88
}
