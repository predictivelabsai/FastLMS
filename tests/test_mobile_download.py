from fasthtml.common import to_xml

from components.landing import ANDROID_APK_URL, fastlearn_landing


def test_fastlearn_landing_links_latest_android_release():
    markup = to_xml(fastlearn_landing("en"))

    assert ANDROID_APK_URL.endswith("/releases/latest/download/fastlearn-mobile-latest.apk")
    assert markup.count(ANDROID_APK_URL) >= 3
    assert 'id="mobile"' in markup
    assert "Early access for Android" in markup
    assert 'class="apk-badge-ic"' in markup
    assert 'aria-hidden="true"' in markup
    assert "Get the mobile app" in markup
    assert "GET &amp; INSTALL" in markup
    assert "APK for Android" in markup
