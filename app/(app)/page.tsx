import { ApplyThemeScript } from '@/components/theme-toggle';
import WelcomeDynamic from '@/components/welcome-dynamic';
import { VoiceWidget } from '@/components/widget';

export default function Page() {
  return (
    <div className="bg-background">
      <ApplyThemeScript />
      <WelcomeDynamic />
      <VoiceWidget />
    </div>
  );
}
