import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import useGlobalReducer from "../hooks/useGlobalReducer";

const API = import.meta.env.VITE_BACKEND_URL;

const Misplanes = () => {
  const { store } = useGlobalReducer();
  const navigate = useNavigate();

  const [plans, setPlans] = useState([]);
  const [planActive, setPlanActive] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlanes = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const resp = await fetch(`${API}/api/myplans`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await resp.json();
        if (data.success) setPlans(data.data);
      } catch {
        setError("No se pudieron cargar los planes");
      } finally {
        setLoading(false);
      }
    };
    fetchPlanes();
  }, []);

  const handleEliminar = async (planId) => {
    try {
      const token = localStorage.getItem("token");
      const resp = await fetch(`${API}/api/myplans/${planId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await resp.json();
      if (data.success) {
        setPlans((prev) => prev.filter((plan) => plan.id !== planId));
        if (planActive?.id === planId) setPlanActive(null);
      }
    } catch {
      setError("No se pudo eliminar el plan");
    }
  };

  const renderPlan = (plan) => {
    const data = plan.plan_data;

    if (plan.tipo_plan === "workout") {
      return (
        <div>
          <h5 className="text-white fw-bold mb-1">{data.plan_name}</h5>
          <p className="text-secondary mb-1">Objetivo: {data.goal}</p>
          <p className="text-secondary mb-3">
            {data.duration_weeks} semanas · {data.weekly_structure?.days_per_week} días/semana
          </p>

          {data.weeks?.map((weekBlock) => (
            <div key={weekBlock.week_range} className="mb-4 p-3 rounded-2 bg-dark border border-secondary">
              <p className="text-danger fw-semibold mb-1">{weekBlock.week_range} — {weekBlock.phase}</p>
              <p className="text-secondary small mb-3">{weekBlock.focus}</p>

              {weekBlock.sessions?.map((session) => (
                <div key={session.day} className="mb-3 ps-3 border-start border-danger">
                  <p className="text-white fw-semibold mb-1">{session.day} — {session.type}</p>
                  <p className="text-secondary small mb-2">Calentamiento: {session.warmup}</p>

                  {session.exercises?.map((ejercicio) => (
                    <div key={ejercicio.name} className="mb-2">
                      <p className="text-white small mb-0">
                        <span className="text-danger fw-semibold">•</span> {ejercicio.name} — {ejercicio.sets} series x {ejercicio.reps} · {ejercicio.rest_seconds}s descanso
                      </p>
                      {ejercicio.notes && (
                        <p className="text-secondary mb-0" style={{ fontSize: "0.75rem" }}>{ejercicio.notes}</p>
                      )}
                    </div>
                  ))}

                  <p className="text-secondary small mt-2">Vuelta a la calma: {session.cooldown}</p>
                </div>
              ))}
            </div>
          ))}

          {data.general_tips?.length > 0 && (
            <div className="mt-3 p-3 rounded-2 bg-dark border border-secondary">
              <p className="text-danger text-uppercase fw-semibold mb-2 small">Consejos generales</p>
              {data.general_tips.map((tip) => (
                <p key={tip} className="text-secondary small mb-1">• {tip}</p>
              ))}
            </div>
          )}

          {data.progression_notes && (
            <p className="text-secondary small mt-3">{data.progression_notes}</p>
          )}
        </div>
      );
    }

    // Dieta
    return (
      <div>
        <h5 className="text-white fw-bold mb-1">{data.plan_name}</h5>
        <p className="text-secondary mb-1">Objetivo: {data.goal}</p>
        <p className="text-secondary mb-3">
          {data.daily_calories} kcal/día · Proteínas: {data.macros?.protein_g}g · Carbohidratos: {data.macros?.carbs_g}g
        </p>

        {data.weekly_menu?.map((weekBlock) => (
          <div key={weekBlock.week_range} className="mb-4 p-3 rounded-2 bg-dark border border-secondary">
            <p className="text-danger fw-semibold mb-3">{weekBlock.week_range} — {weekBlock.phase}</p>

            {weekBlock.days?.map((day) => (
              <div key={day.day} className="mb-3 ps-3 border-start border-danger">
                <p className="text-white fw-semibold mb-2">{day.day}</p>

                {day.meals?.map((meal) => (
                  <div key={meal.meal_type} className="mb-2">
                    <p className="text-secondary small mb-1">
                      <span className="text-danger fw-semibold">{meal.meal_type}</span>
                      {meal.time && ` · ${meal.time}`} — {meal.total_calories} kcal
                    </p>
                    {meal.foods?.map((food) => (
                      <p key={food.name} className="text-white small mb-0 ps-2">
                        • {food.name} · {food.quantity} · {food.calories} kcal
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}

        {data.general_tips?.length > 0 && (
          <div className="mt-3 p-3 rounded-2 bg-dark border border-secondary">
            <p className="text-danger text-uppercase fw-semibold mb-2 small">Consejos generales</p>
            {data.general_tips.map((tip) => (
              <p key={tip} className="text-secondary small mb-1">• {tip}</p>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-vh-100 pt-5 mt-5 bg-black">
      <div className="container">

        {planActive ? (
          // ── Vista detalle del plan ──
          <div>
            <button
              className="btn btn-outline-secondary btn-sm mb-4 d-flex align-items-center gap-2"
              onClick={() => setPlanActive(null)}
            >
              ← Volver a mis planes
            </button>

            <div className="p-4 rounded-3 bg-dark border border-secondary">
              <p className="text-danger text-uppercase fw-semibold small mb-3">
                {planActive.tipo_plan === "workout" ? "Plan de ejercicio" : "Plan de dieta"}
              </p>
              {renderPlan(planActive)}
            </div>
          </div>

        ) : (
          // ── Vista lista de planes ──
          <div>
            {/* Cabecera */}
            <div className="d-flex align-items-center justify-content-between mb-4">
              <div>
                <p className="text-danger text-uppercase fw-semibold small mb-1">Dashboard</p>
                <h2 className="text-white fw-bold mb-0">Mis planes</h2>
              </div>
              <button
                className="btn btn-danger rounded-pill px-4"
                onClick={() => navigate("/subscription-plans")}
              >
                + Nuevo plan
              </button>
            </div>

            {/* Estados */}
            {loading && (
              <div className="d-flex align-items-center gap-2 text-secondary py-4">
                <div className="spinner-border spinner-border-sm text-danger" role="status"></div>
                Cargando planes...
              </div>
            )}

            {error && <p className="text-danger small">{error}</p>}

            {!loading && plans.length === 0 && (
              <div className="text-center py-5 border border-secondary rounded-3">
                <p className="text-secondary mb-3">Aún no tienes planes generados</p>
                <button
                  className="btn btn-danger rounded-pill px-4"
                  onClick={() => navigate("/subscription-plans")}
                >
                  Crear mi primer plan
                </button>
              </div>
            )}

            {/* Lista de planes */}
            <div className="d-flex flex-column gap-3">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className="d-flex align-items-center justify-content-between p-3 rounded-3 bg-dark border border-secondary"
                >
                  <div>
                    <p className="text-white fw-semibold mb-1">
                      {plan.plan_data?.plan_name || "Plan generado"}
                    </p>
                    <p className="text-secondary small mb-0">
                      {plan.tipo_plan === "workout" ? "Ejercicio" : "Dieta"} · {plan.plan_data?.duration_weeks} semanas
                    </p>
                  </div>

                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-danger btn-sm rounded-pill px-3"
                      onClick={() => setPlanActive(plan)}
                    >
                      Ver plan
                    </button>
                    <button
                      className="btn btn-outline-secondary btn-sm rounded-pill px-3"
                      onClick={() => handleEliminar(plan.id)}
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Volver al perfil */}
            {plans.length > 0 && (
              <button
                className="btn btn-outline-secondary mt-4 d-flex align-items-center gap-2"
                onClick={() => navigate("/profile")}
              >
                ← Volver al perfil
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Misplanes;
