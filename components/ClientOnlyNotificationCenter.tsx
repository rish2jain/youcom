"use client";

import { useEffect, useState } from "react";
import { NotificationCenter } from "./NotificationSystem";
import { useNotificationContext } from "@/app/notifications/NotificationProvider";

interface ClientOnlyNotificationCenterProps {
  maxVisible?: number;
  showResolved?: boolean;
  autoHide?: boolean;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
}

export default function ClientOnlyNotificationCenter(
  props: ClientOnlyNotificationCenterProps
) {
  const [hasMounted, setHasMounted] = useState(false);
  const { notifications } = useNotificationContext();

  useEffect(() => {
    setHasMounted(true);
  }, []);

  // Absolutely ensure this only runs on client
  if (typeof window === "undefined" || !hasMounted) {
    return null;
  }

  // Render directly without portal to simplify
  return <NotificationCenter {...props} notifications={notifications} />;
}
