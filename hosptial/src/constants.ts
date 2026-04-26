import { 
  LayoutDashboard, 
  Users, 
  Stethoscope, 
  Pill, 
  Beaker, 
  CreditCard, 
  Settings,
  Search,
  Bell,
  User,
  ChevronLeft
} from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'overview', label: 'الرئيسية', icon: LayoutDashboard },
  { id: 'patients', label: 'سجل المرضى', icon: Users },
  { id: 'clinical', label: 'المركز الطبي', icon: Stethoscope },
  { id: 'master-data', label: 'مركز البيانات', icon: Beaker },
  { id: 'pharmacy', label: 'الصيدلية', icon: Pill },
  { id: 'laboratory', label: 'المختبر', icon: Beaker },
  { id: 'billing', label: 'النظام المالي', icon: CreditCard },
  { id: 'settings', label: 'الإعدادات', icon: Settings },
];

export interface NavItem {
  id: string;
  label: string;
  icon: any;
}
