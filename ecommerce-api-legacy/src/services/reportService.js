const { PAYMENT_STATUS } = require('../config/constants');

function createReportService({ models }) {
    async function financialReport() {
        const rows = await models.courses.findAllWithEnrollments();
        const byCourse = new Map();

        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const courseData = byCourse.get(row.course_id);
            if (row.status === PAYMENT_STATUS.PAID) courseData.revenue += row.amount;
            courseData.students.push({
                student: row.student ?? 'Unknown',
                paid: row.amount ?? 0,
            });
        }

        return [...byCourse.values()];
    }

    return { financialReport };
}

module.exports = { createReportService };
