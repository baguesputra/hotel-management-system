from datetime import date
from decimal import Decimal
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.room import Room, RoomPricing, SeasonType


class PricingService:

    def _is_date_in_range(self, target: date, start_mmdd: str, end_mmdd: str) -> bool:
        """
        Cek apakah tanggal target jatuh dalam range MM-DD.
        Mendukung range yang melewati tahun baru (misal: 12-15 s/d 01-05).
        """
        year = target.year
        start_month, start_day = map(int, start_mmdd.split("-"))
        end_month, end_day = map(int, end_mmdd.split("-"))

        start = date(year, start_month, start_day)
        end = date(year, end_month, end_day)

        # handle range yang melewati tahun baru
        if start > end:
            return target >= start or target <= end
        return start <= target <= end

    async def get_price_for_date(
        self,
        db: AsyncSession,
        room: Room,
        target_date: date
    ) -> Decimal:
        """Hitung harga kamar untuk tanggal tertentu."""
        result = await db.execute(
            select(RoomPricing).where(RoomPricing.room_id == room.id)
        )
        pricings = result.scalars().all()

        # cek apakah tanggal masuk ke season tertentu
        # prioritas: holiday > peak > regular
        priority_order = [SeasonType.HOLIDAY, SeasonType.PEAK, SeasonType.REGULAR]

        for season in priority_order:
            for pricing in pricings:
                if pricing.season_type == season:
                    if self._is_date_in_range(target_date, pricing.start_date, pricing.end_date):
                        return Decimal(str(room.base_price)) * Decimal(str(pricing.price_multiplier))

        # tidak ada season rule → pakai base price
        return Decimal(str(room.base_price))

    async def calculate_total(
        self,
        db: AsyncSession,
        room: Room,
        check_in: date,
        check_out: date
    ) -> tuple[Decimal, Decimal]:
        """
        Hitung total harga untuk periode menginap.
        Return: (price_per_night, total_amount)
        Menggunakan harga hari pertama sebagai price_per_night representatif.
        """
        total = Decimal("0")
        current = check_in

        while current < check_out:
            daily_price = await self.get_price_for_date(db, room, current)
            total += daily_price
            # geser ke hari berikutnya
            from datetime import timedelta
            current += timedelta(days=1)

        total_nights = (check_out - check_in).days
        price_per_night = await self.get_price_for_date(db, room, check_in)

        return price_per_night, total


pricing_service = PricingService()