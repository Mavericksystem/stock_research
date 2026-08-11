import EventsSidebar from "../features/anomalies/components/EventsSidebar";

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
  onEventSelect: (question: string) => void;
}

export default function Sidebar({
  open,
  onToggle,
  onEventSelect,
}: SidebarProps) {
  return (
    <EventsSidebar
      open={open}
      onToggle={onToggle}
      onEventSelect={onEventSelect}
    />
  );
}
