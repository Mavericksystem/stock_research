import EventsSidebar from "../features/anomalies/components/EventsSidebar";

export default function Sidebar({ open, onToggle, onEventSelect }) {
  return <EventsSidebar open={open} onToggle={onToggle} onEventSelect={onEventSelect} />;
}