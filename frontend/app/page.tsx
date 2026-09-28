"use client";

import { useState } from "react";
import { LANGUAGES } from "./languages";

const stations = [
  { year: "610م", title: "بداية الرسالة", place: "مكة المكرمة", icon: "✦" },
  { year: "622م", title: "الهجرة", place: "مكة → المدينة", icon: "↗" },
  { year: "624م", title: "بدر", place: "بدر", icon: "◈" },
  { year: "630م", title: "فتح مكة", place: "مكة المكرمة", icon: "⌖" },
  { year: "632م", title: "المدينة", place: "المدينة المنورة", icon: "◆" }
];

export default function Home() {
  const [language, setLanguage] = useState("ar");
  const [question, setQuestion] = useState("");

  return (
    <main className="page">
      <header className="nav">
        <div className="brand">
          <div className="brand-mark">ر</div>
          <div>
            <strong>رِسالة</strong>
            <span>أطلس معرفي تفاعلي</span>
          </div>
        </div>

        <div className="nav-actions">
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((item) => (
              <option key={item.code} value={item.code}>{item.name}</option>
            ))}
          </select>
          <button className="ghost">عن المشروع</button>
        </div>
      </header>

      <section className="hero">
        <div className="glow" />
        <div className="hero-copy">
          <div className="eyebrow">رحلة عبر الزمان والمكان</div>
          <h1>اكتشف التاريخ<br /><span>من قلب المكان</span></h1>
          <p>
            تجربة معرفية تفاعلية تربط الأحداث التاريخية بالمكان والزمان،
            وتتيح للزائر طرح الأسئلة واستكشاف الإجابات الموثقة.
          </p>

          <div className="ask-box">
            <div className="ask-icon">⌕</div>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="اسأل عن حدث، مكان، أو فترة تاريخية..."
            />
            <button>ابدأ الرحلة</button>
          </div>

          <div className="trust-row">
            <span>◉ مصادر موثقة</span>
            <span>◉ دعم 30+ لغة</span>
            <span>◉ إجابات مرتبطة بالمصادر</span>
          </div>
        </div>

        <div className="atlas">
          <div className="atlas-top">
            <span>INTERACTIVE ATLAS</span>
            <span>610 — 632م</span>
          </div>
          <div className="map">
            <div className="grid" />
            <div className="route route-a" />
            <div className="route route-b" />
            <div className="pin pin-1"><b>610</b><small>مكة</small></div>
            <div className="pin pin-2"><b>622</b><small>الهجرة</small></div>
            <div className="pin pin-3"><b>632</b><small>المدينة</small></div>
            <div className="compass">N<br /><span>✦</span></div>
          </div>
          <div className="atlas-bottom">
            <span>الطبقة: الأحداث التاريخية</span>
            <span>3D / MAP</span>
          </div>
        </div>
      </section>

      <section className="timeline-section">
        <div className="section-heading">
          <div>
            <div className="eyebrow">TIMELINE</div>
            <h2>محطات الرحلة</h2>
          </div>
          <span>استكشف ←</span>
        </div>

        <div className="timeline">
          {stations.map((station) => (
            <article className="station" key={station.year}>
              <div className="station-icon">{station.icon}</div>
              <span className="year">{station.year}</span>
              <h3>{station.title}</h3>
              <p>{station.place}</p>
            </article>
          ))}
        </div>
      </section>

      <footer>
        <span>رِسالة — مشروع معرفي مدعوم بالذكاء الاصطناعي</span>
        <span>نسخة MVP</span>
      </footer>
    </main>
  );
}
