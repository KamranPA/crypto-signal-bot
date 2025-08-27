def get_signal(df):
    print(f"📊 get_signal فراخوانی شد با {len(df)} کندل")
    
    try:
        # 1. شکست
        signal = apply_breakout_strategy(df)
        if signal:
            print(f"✅ سیگنال شکست: {signal['signal']} | ورود: {signal['entry']}")
            return {**signal, 'priority': 1}

        # 2. روند
        signal = apply_trend_strategy(df)
        if signal:
            print(f"✅ سیگنال روند: {signal['signal']} | ورود: {signal['entry']}")
            return {**signal, 'priority': 2}

        # 3. رنج
        if is_range_regime(df):
            print("🔍 بازار در رنج است، بررسی استراتژی رنج...")
            signal = apply_range_strategy(df)
            if signal:
                print(f"✅ سیگنال رنج: {signal['signal']} | ورود: {signal['entry']}")
                return {**signal, 'priority': 3}
        else:
            print("❌ بازار در رنج نیست، استراتژی رنج فعال نمی‌شود")

        print("❌ هیچ سیگنالی تولید نشد")
        return None

    except Exception as e:
        print(f"❌ خطا در get_signal: {e}")
        return None
