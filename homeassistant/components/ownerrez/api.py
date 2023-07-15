import aiohttp
from datetime import datetime, timedelta, date
import logging
import pytz

from enum import Enum

# _LOGGER = logging.getLogger("omnilogic")

from .const import OR_URL1, OR_URL2


class OwnerRes:
    def __init__(self, username, password, DaysInFuture) -> None:
        self.username = username
        self.password = password
        self.daysinfuture = DaysInFuture
        self.verbose = True
        self.logged_in = False
        self.retry = 5
        self._auth = aiohttp.BasicAuth(username, password)
        self._Rental_Property = []

    async def close(self):
        await self._session.close()

    @property
    def Rental_Property(self):
        """Return the Rental Properties"""
        return self._Rental_Property

    async def testconnection(self):
        api_url = OR_URL1 + "/properties"
        async with aiohttp.ClientSession(auth=self._auth) as session:
            try:
                async with session.get(api_url) as resp:
                    if resp.status != 200:
                        jresult = resp.reason
                    else:
                        jresult = "OK"
                    await session.close()
            except:
                jresult = "URLNotFound"
        return jresult

    async def getproperties(self):
        # Jr2 = dict()
        PResults = []
        self._Rental_Property = []
        api_url = OR_URL1 + "/properties"
        async with aiohttp.ClientSession(auth=self._auth) as session:
            async with session.get(api_url) as resp:
                jresult = await resp.json()
                await session.close()

                for Jr2 in jresult:
                    Jr2["auth"] = self._auth
                    Jr2["daysinfuture"] = self.daysinfuture
                    self._Rental_Property.append(Rental_Property(Jr2))

            for propcalendar in self._Rental_Property:
                await propcalendar.update()

            return self._Rental_Property


class Rental_Property:
    def __init__(self, RentProp) -> None:
        self.Key = RentProp["Key"]
        self.Pname = RentProp["Name"]
        self.Id = RentProp["Id"]

        if "TimeZoneId" in RentProp:
            self.TimeZone = RentProp["TimeZoneId"]
        else:
            # Need to fix this.  If property TZ is missing I should take it from the Account Profile
            self.TimeZone = "America/New_York"


        self.daysinfuture = RentProp["daysinfuture"]
        self.auth = RentProp["auth"]
        self._state = None
        self.calendar = []

    @property
    def state(self):
        """Return the Rental Properties"""
        return self._state

    async def update(self):
        start_of_events = datetime.now().date()
        end_of_events = start_of_events + timedelta(days=self.daysinfuture)
        events_start = start_of_events.strftime("%Y-%m-%d")
        events_end = end_of_events.strftime("%Y-%m-%d")

        date_format = "%Y-%m-%dT%H:%M:%S"
        tz = pytz.timezone(self.TimeZone)
        self.calendar = []

        api_url = (
            OR_URL2
            + "/bookings?property_ids="
            + str(self.Id)
            + "&from="
            + events_start
            + "&to="
            + events_end
        )

        jresult = {}
        # resp = ""
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    jresult = await resp.json()

                    # Did we find any bookings or blocks (indicated under th items list)
                    if "items" in jresult:
                        for bookingrecord in jresult["items"]:
                            if bookingrecord["is_block"] == False:
                                api_url = (
                                    "https://api.ownerreservations.com/v2/bookings/"
                                    + str(bookingrecord["id"])
                                )

                                async with session.get(api_url) as resp:
                                    bresult = await resp.json()

                                # There may not be a checkin / checkout time defined in the result
                                if "check_in" in bresult:
                                    checkintime = bresult["check_in"] + ":00"
                                    checkouttime = bresult["check_out"] + ":00"
                                else:
                                    checkintime = "12:00:01"
                                    checkouttime = "12:00:01"

                                booking_arrival = (
                                    bookingrecord["arrival"] + "T" + checkintime
                                )
                                booking_departure = (
                                    bookingrecord["departure"] + "T" + checkouttime
                                )

                                booking_arrival_dt = datetime.strptime(
                                    booking_arrival, date_format
                                )
                                booking_arrival_tz = tz.localize(booking_arrival_dt)

                                booking_departure_dt = datetime.strptime(
                                    booking_departure, date_format
                                )
                                booking_departure_tz = tz.localize(booking_departure_dt)

                                # Determine Calendar State
                                JT = tz.localize(datetime.now())
                                self._state = True

                                api_url = (
                                    "https://api.ownerreservations.com/v2/guests/"
                                    + str(bookingrecord["guest_id"])
                                )

                                async with session.get(api_url) as resp:
                                    guest_name = await resp.json()

                                new_record = {
                                    "start": booking_arrival_tz,
                                    "end": booking_departure_tz,
                                    "summary": guest_name["first_name"]
                                    + " "
                                    + guest_name["last_name"]
                                    + " TZ:"
                                    + tz.zone,
                                    "guestname": guest_name["first_name"]
                                    + " "
                                    + guest_name["last_name"],
                                    "orid": self.Id,
                                }
                                self.calendar.append(new_record)
        await session.close()
