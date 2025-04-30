# ui/instructions.py

def top_bar() -> str:
    return """
    <div style="height: 4px; background: linear-gradient(to right, #4dd6c1, #37b8a4, #2aa395); width: 100%;"></div>
    """

def instructions_header(primary_color: str, text_color: str) -> str:
    return f"""
    <div style="padding: 0 24px 0 24px; display: flex; align-items: center;">
        <div style="background-color: {primary_color}33; border: 2px solid {primary_color}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" color="{primary_color}" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
        </div>
        <h2 style="margin: 0; font-family: 'Inter', sans-serif; font-size: 1.4rem; color: {text_color};">Instructions</h2>
    </div>
    """

def subtitle(text_color: str) -> str:
    return f"""
    <div style="padding: 0 24px 15px 65px; margin-top: -15px;">
        <p style="font-family: 'Inter', sans-serif; color: {text_color}; font-size: 0.95rem; line-height: 1.25rem; opacity: 0.5; margin: 0;">
            Follow these steps to detect coffee leaf diseases
        </p>
    </div>
    """

def step_item(i: int, step: str, primary_color: str, text_color: str) -> str:
    return f"""
    <div style="display: flex; align-items: center; padding: 12px 20px 5px 50px;">
        <div style="background-color: {primary_color}; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; flex-shrink: 0;">
            <span style="font-weight: 600; font-size: 15px; color: white">{i}</span>
        </div>
        <p style="letter-spacing: 0.4px; font-family: 'Inter', sans-serif; font-size: 0.95rem; line-height: 1.25rem; margin: 0; color: {text_color};">{step}</p>
    </div>
    """

def note_banner(primary_color: str) -> str:
    return f"""
    <div style="border-radius: 4px; margin: 20px 24px 0; padding: 12px 16px 0; display: flex; align-items: flex-start;">
        <p style="font-family: 'Inter', sans-serif; margin: 0; color: {primary_color};"></p>
    </div>
    """